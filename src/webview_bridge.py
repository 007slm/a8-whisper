
import os
import json
import threading
import time
import keyboard
import pyautogui
import webview
from src.api_server import emit_status
# asr/llm lazy imports inside to save startup time
# BUT AudioRecorder imports numpy, which must be loaded in main thread for frozen app stability
from src.core.audio import AudioRecorder

CONFIG_FILE = os.path.expanduser("~/.a8qingyu_config.json")

class WebviewBridge:
    def __init__(self):
        self._main_window = None
        self._overlay_window = None
        self._config = self._load_config()
        
        # Backend components
        self._recorder = None
        self._asr = None
        self._llm = None
        self.is_processing = False
        self.stop_requested = False
        self._initialized = False
        
        # 【延迟初始化】不在这里启动线程，等 set_windows 调用后再启动

    def _set_windows(self, main, overlay):
        self._main_window = main
        self._overlay_window = overlay
        
        # 窗口设置后，延迟启动后台任务
        if not self._initialized:
            self._initialized = True
            # 延迟 1 秒确保 webview 完全就绪
            def _delayed_init():
                import time
                time.sleep(3)
                print("[INFO] Starting background initialization...")
                threading.Thread(target=self._init_models, daemon=True).start()
                threading.Thread(target=self._setup_hotkey, daemon=True).start()
            threading.Thread(target=_delayed_init, daemon=True).start()

    def _load_config(self):
        config = {
            "asr_model": "large-v3",
            "llm_enabled": True,
            "use_cloud": False,  # Default to Local
            "hotkey": "left ctrl+left windows",
            "overlay_enabled": True,
            "sound_enabled": False,
            "models_status": {} 
        }
        
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    config.update(saved)
            except:
                pass
        
        # Check Local Model Status
        model_size = config.get("asr_model", "large-v3")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        local_path = os.path.join(project_root, "models", f"faster-whisper-{model_size}", "config.json")
        
        config["models_status"] = {
            model_size: os.path.exists(local_path)
        }
        
        return config

    def _refresh_model_status(self):
        # Check Local Model Status
        model_size = self._config.get("asr_model", "large-v3")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        local_path = os.path.join(project_root, "models", f"faster-whisper-{model_size}", "config.json")
        
        self._config["models_status"] = {
            model_size: os.path.exists(local_path)
        }

    def _save_to_disk(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Config save failed: {e}")

    # --- Exposed API to JS ---
    # 【原则】所有 API 方法必须秒返回，重活放后台线程
    
    def requestConfig(self):
        # Fire-and-Forget: 通过回调推送 config
        def _push():
            self._emit_to_all("config", self._config)
        threading.Thread(target=_push, daemon=True).start()
        return {"status": "ok"}

    def saveConfig(self, config):
        # Fire-and-Forget: 后台更新，立即返回
        def _save():
            self._config.update(config)
            self._save_to_disk()
            
            # Re-check model status (e.g. if user switched model)
            self._refresh_model_status()
            
            self._emit_to_all("config", self._config)
        threading.Thread(target=_save, daemon=True).start()
        return {"status": "ok"}

    def minimizeWindow(self):
        # Fire-and-Forget
        def _do():
            try:
                if self._main_window:
                    self._main_window.minimize()
            except: pass
        threading.Thread(target=_do, daemon=True).start()
        return {"status": "ok"}

    def closeWindow(self):
        # Fire-and-Forget: 隐藏到托盘
        def _do():
            try:
                if self._main_window:
                    self._main_window.hide()
            except: pass
        threading.Thread(target=_do, daemon=True).start()
        return {"status": "ok"}

    # Combined Window + Init logic
    def _set_window_internal(self, window):
        self._main_window = window
        self._window = window # For style fix
        
        # Apply Resize Fix
        threading.Thread(target=self._apply_window_styles, daemon=True).start()
        
        # Trigger Init Logic if not already started
        if not self._initialized:
            self._initialized = True
            def _delayed_init():
                time.sleep(1) # Wait for window to show
                print("[INFO] Starting background initialization...")
                threading.Thread(target=self._init_models, daemon=True).start()
                threading.Thread(target=self._setup_hotkey, daemon=True).start()
            threading.Thread(target=_delayed_init, daemon=True).start()

    def _apply_window_styles(self):
        time.sleep(0.5)
        if not self._window:
            return
        
        try:
            import ctypes
            
            hwnd = 0
            # Try to get Handle from pywebview window object
            if hasattr(self._window, 'gui') and hasattr(self._window.gui, 'Handle'):
                hwnd = int(self._window.gui.Handle)
            else:
                hwnd = ctypes.windll.user32.GetForegroundWindow()

            if hwnd:
                print(f"[INFO] Applying Resize Styles to HWND: {hwnd}")
                GWL_STYLE = -16
                WS_THICKFRAME = 0x00040000
                WS_CAPTION = 0x00C00000
                
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
                # Keep existing style but Ensure ThickFrame (Resize) and No Caption
                target_style = (style | WS_THICKFRAME) & ~WS_CAPTION
                
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, target_style)
                ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0037)
                
                # Fix: Show window only after styles are applied to prevent white screen
                self._window.show()
        except Exception as e:
            print(f"[ERROR] Failed to apply window styles: {e}")

    def startDrag(self):
        # Native Windows Drag (Smoothest)
        try:
            import ctypes
            # Release Capture from this thread (might fail if not UI thread, but worth trying)
            ctypes.windll.user32.ReleaseCapture()
            
            hwnd = 0
            if self._window and hasattr(self._window, 'gui') and hasattr(self._window.gui, 'Handle'):
                hwnd = int(self._window.gui.Handle)
            
            # Fallback
            if not hwnd:
                hwnd = ctypes.windll.user32.GetForegroundWindow()

            if hwnd:
                print(f"[INFO] Starting Drag on HWND: {hwnd}")
                # Send WM_NCLBUTTONDOWN (0xA1) with HTCAPTION (2)
                ctypes.windll.user32.SendMessageW(hwnd, 0xA1, 2, 0)
            else:
                print("[ERROR] Drag failed: No Window Handle")
        except Exception as e:
            print(f"Drag failed: {e}")
        return {"status": "ok"} 

    def maximizeWindow(self):
        # Fire-and-Forget
        def _do():
            try:
                if self._main_window:
                    self._main_window.toggle_fullscreen()
            except: pass
        threading.Thread(target=_do, daemon=True).start()
        return {"status": "ok"}

    def downloadModel(self, model_name):
        print(f"Downloading model: {model_name}")
        threading.Thread(target=self._download_worker, args=(model_name,), daemon=True).start()
        return {"status": "ok"}

    def checkLLMFileExists(self):
        # Frontend logic calls this to check if LLM is installed
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        llm_path = os.path.join(project_root, "models", "qwen2.5-coder-7b-instruct-q4_k_m.gguf")
        exists = os.path.exists(llm_path)
        print(f"[INFO] Checking LLM File: {llm_path} -> {exists}")
        return exists

    def downloadLLMModel(self):
        print("Downloading LLM Model...")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        # Using huggingface-cli or requests to download GGUF?
        # For now, let's map it to _download_worker but with a special flag or separate worker
        # Since logic is different (single file vs directory), let's create a specific worker or handle it here
        threading.Thread(target=self._download_llm_worker, daemon=True).start()
        return {"status": "ok"}

    def _download_llm_worker(self):
        model_id = "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
        filename = "qwen2.5-coder-7b-instruct-q4_k_m.gguf"
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        models_dir = os.path.join(project_root, "models")
        os.makedirs(models_dir, exist_ok=True)
        local_path = os.path.join(models_dir, filename)

        print(f"[INFO] Downloading LLM to {local_path}...")
        
        try:
             from huggingface_hub import hf_hub_download
             
             # Pulse progress
             stop_pulse = False
             def _pulse():
                p = 0.1
                while not stop_pulse and p < 0.95:
                    time.sleep(0.5)
                    p += 0.02
                    self._emit_to_all("llm_progress", min(p, 0.99)) # Frontend expects number directly? 
                    # App.tsx: (bridge as any).onLlmDownloadProgress((progress: number)
            
             threading.Thread(target=_pulse, daemon=True).start()

             hf_hub_download(repo_id=model_id, filename=filename, local_dir=models_dir, local_dir_use_symlinks=False)
             
             stop_pulse = True
             self._emit_to_all("llm_progress", 1.0)
             print("[OK] LLM Download Complete")
             
        except Exception as e:
            print(f"[ERROR] LLM Download Failed: {e}")
            self._emit_to_all("llm_progress", -1.0)

    def _download_worker(self, model_name):
        # Use huggingface_hub to download Faster-Whisper models
        try:
            from huggingface_hub import snapshot_download
            import os
            
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            output_dir = os.path.join(project_root, "models", f"faster-whisper-{model_name}")
            
            print(f"[INFO] Downloading {model_name} to {output_dir}...")
            
            # Set up Hugging Face mirror for China users
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
            
            # Progress simulation
            stop_pulse = False
            def _pulse():
                p = 0.1
                while not stop_pulse and p < 0.95:
                    time.sleep(1.0)  # Slower pulse for large downloads
                    p += 0.02
                    self._emit_to_all("model_progress", {"model": model_name, "progress": min(p, 0.99)})
            
            threading.Thread(target=_pulse, daemon=True).start()
            
            # Download from Systran repository
            repo_id = f"Systran/faster-whisper-{model_name}"
            snapshot_download(
                repo_id=repo_id,
                local_dir=output_dir,
                local_dir_use_symlinks=False,
                resume_download=True,
                max_workers=4
            )
            
            stop_pulse = True
            
            print(f"[OK] Download complete: {model_name}")
            self._emit_to_all("model_progress", {"model": model_name, "progress": 1.0})
            
            # Refresh Status
            self._refresh_model_status()
            self._emit_to_all("config", self._config)
            
            # Try to initialize the ASR engine with the new model
            try:
                from src.core.asr import asr_engine
                asr_engine.model = None  # Reset current model
                asr_engine.initialize(model_size=model_name)
                print(f"[OK] ASR engine initialized with {model_name}")
            except Exception as init_e:
                print(f"[WARN] Failed to auto-initialize ASR: {init_e}")
            
        except ImportError as e:
            print(f"[ERROR] Missing dependency: {e}")
            print("[ERROR] Please install: pip install huggingface_hub")
            self._emit_to_all("model_progress", {"model": model_name, "progress": -1})
        except Exception as e:
            print(f"[ERROR] Download failed: {e}")
            self._emit_to_all("model_progress", {"model": model_name, "progress": -1})

    def openExternal(self, url):
        # Fire-and-Forget
        def _do():
            import webbrowser
            webbrowser.open(url)
        threading.Thread(target=_do, daemon=True).start()
        return {"status": "ok"}

    # --- Backend Logic (Copied/Adapted from main_backend_only.py) ---

    def _emit_to_all(self, event_type, data):
        """Send event to both windows - SYNCHRONOUS (called from background threads when UI is idle)"""
        print(f"[DEBUG] Emitting event: {event_type} with data: {data}")
        js = f"window.handlePywebviewMessage({{type: '{event_type}', data: {json.dumps(data)}}})"
        try:
            if self._main_window:
                print(f"[DEBUG] Sending to main window: {js[:100]}...")
                self._main_window.evaluate_js(js)
            else:
                print("[DEBUG] Main window not available")
        except Exception as e:
            print(f"[DEBUG] Error sending to main window: {e}")
        try:
            if self._overlay_window:
                self._overlay_window.evaluate_js(js)
        except Exception as e:
            pass
            
    def _setup_hotkey(self):
        # Polling Mode: Most stable approach for Pywebview + WinForms
        print("[OK] Hotkey detection thread started (Ctrl+LeftWin)")
        self._key_state = {'ctrl': False, 'win': False, 'was_combo': False}
        
        while True:
            try:
                # 50ms Polling
                time.sleep(0.05)
                
                # Check status
                is_ctrl = keyboard.is_pressed('ctrl')
                is_win = keyboard.is_pressed('left windows') or keyboard.is_pressed('right windows')
                
                # Debug: Print if either is pressed (throttled)
                # if is_ctrl or is_win:
                #    print(f"Key State - Ctrl: {is_ctrl}, Win: {is_win}")
                
                is_combo = is_ctrl and is_win
                was_combo = self._key_state['was_combo']
                
                if is_combo and not was_combo:
                     # Pressed
                     print("[HOTKEY] Hotkey Detected: Ctrl+Win")
                     threading.Thread(target=self._trigger_start, daemon=True).start()
                elif not is_combo and was_combo:
                     # Released
                     print("[HOTKEY] Hotkey Released")
                     threading.Thread(target=self._trigger_stop, daemon=True).start()
                     
                self._key_state['was_combo'] = is_combo
            except Exception as e:
                print(f"[ERROR] Hotkey Loop Error: {e}")
                time.sleep(1)
    
    def _trigger_start(self):
        if not self.is_processing and (not self._recorder or not self._recorder.recording):
            self._start_recording()
    
    def _trigger_stop(self):
        if self._recorder and self._recorder.recording:
            self._stop_and_process()

    def _start_recording(self):
        if self.is_processing or (self._recorder and self._recorder.recording): return
        print("Start Recording...")
        
        # Native Overlay: Show via WebSocket
        emit_status("app_state", "RECORDING")
        self._emit_to_all("app_state", "recording")
        
        if not self._recorder:
            # AudioRecorder is now imported at top-level to fix numpy threading issue
            self._recorder = AudioRecorder()
            
        self._recorder.start()
        threading.Thread(target=self._monitor_levels, daemon=True).start()

    def _stop_and_process(self):
        if not self._recorder or not self._recorder.recording: return
        print("Stop & Process...")
        emit_status("app_state", "PROCESSING")
        self._emit_to_all("app_state", "processing")
        
        audio_file = self._recorder.stop()
        
        if not audio_file:
            self._reset_state()
            return
            
        self.is_processing = True
        threading.Thread(target=self._process_audio, args=(audio_file,)).start()

    def _monitor_levels(self):
        while self._recorder and self._recorder.recording:
            try:
                level = self._recorder.get_amplitude()
                norm = min(level / 2000.0, 1.0)
                
                # Broadcast level to Native Overlay
                emit_status("audio_level", norm)
                
                # Keep existing frontend sync
                js = f"window.handleAudioLevel({norm})"
                if self._main_window: # Only main window now
                     self._main_window.evaluate_js(js)
            except:
                pass # Ignore errors
            time.sleep(0.05) # 20fps

    def _process_audio(self, audio_file):
        try:
            print("Running ASR...")
            emit_status("app_state", "RECOGNIZING")
            self._emit_to_all("app_state", "recognizing")
            
            if not self._asr:
                print("ASR not ready.")
                self._reset_state()
                return

            text = self._asr.transcribe(audio_file)
            print(f"ASR: {text}")
            
            if text:
                corrected_text = text
                # LLM Logic
                if self._config.get("llm_enabled", True) and self._llm:
                    print("Running LLM...")
                    emit_status("app_state", "POLISHING")
                    self._emit_to_all("app_state", "polishing")
                    try:
                        corrected_text = self._llm.correct_text(text)
                        print(f"LLM: {corrected_text}")
                    except Exception as e:
                        print(f"LLM Error: {e}")
                
                # Typing
                emit_status("app_state", "PROCESSING") # Reset to generic busy
                self._emit_to_all("app_state", "typing")
                try:
                    import pyperclip
                    pyperclip.copy(corrected_text)
                    time.sleep(0.05)
                    pyautogui.hotkey('ctrl', 'v')
                except Exception as e:
                    print(f"Paste Error: {e}")

        except Exception as e:
            print(f"Processing Error: {e}")
            emit_status("app_state", "ERROR")
        finally:
            self.is_processing = False
            self._reset_state()

    def _reset_state(self):
        emit_status("app_state", "IDLE") # Hides native overlay
        self._emit_to_all("app_state", "idle")
        # Hide overlay after short delay
        time.sleep(0.5)
        try:
            if self._overlay_window:
                self._overlay_window.hide()
        except: 
            pass

    def _init_models(self):
        # Identical to main_backend_only but uses emit_to_all
        self._emit_to_all("init_status", "正在初始化 ASR...")
        try:
            from src.core.asr import ASREngine
            self._asr = ASREngine()
            self._asr.initialize(model_size=self._config.get("asr_model", "large-v3"))
            self._emit_to_all("init_status", "ASR 就绪")
        except:
             # Fallback
             try:
                 self._asr.initialize(device="cpu", compute_type="int8")
                 self._emit_to_all("init_status", "ASR 就绪 (CPU)")
             except:
                 pass
                 
        # LLM Init...
        if self._config.get("llm_enabled", True):
            # Using robust path finding similar to ASR
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            llm_path = os.path.join(project_root, "models", "qwen2.5-coder-7b-instruct-q4_k_m.gguf")
            
            if os.path.exists(llm_path):
                 self._emit_to_all("init_status", "初始化 LLM...")
                 from src.core.llm import LLMEngine
                 self._llm = LLMEngine()
                 try:
                     self._llm.initialize_local(llm_path, n_gpu_layers=-1)
                     print("[OK] LLM Loaded")
                 except Exception as e:
                     print(f"[ERROR] LLM Init Failed: {e}")
                     self._emit_to_all("init_status", "LLM 加载失败 (非致命)")
            else:
                 print(f"[WARN] Local LLM not found at: {llm_path}")
        else:
            print("[INFO] LLM disabled in config - Skipping")

        # Final Ready Status - Frontend expects "就绪" AND "LLM" to hide spinner
        # See App.tsx: if (e.detail.includes("就绪") && e.detail.includes("LLM"))
        self._emit_to_all("init_status", "服务与LLM就绪")
