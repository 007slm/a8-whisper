# -*- coding: utf-8 -*-
import webview
import threading
import sys
import os
# Fix: Allow multiple OpenMP libraries (torch + ctranslate2 conflict)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
# Fix: Use HF Mirror for China
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# Fix: Import numpy early to prevent "cannot load module more than once" error in frozen app
# Set console encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
import pystray
import subprocess
import socket
import time
import atexit
from PIL import Image, ImageDraw

# LOGGING SETUP FOR RELEASE
# In frozen mode (EXE), redirect stdout/stderr to a file for debugging
if getattr(sys, 'frozen', False):
    log_path = os.path.expanduser("~/.a8qingyu_debug.log")
    try:
        # Open in append mode with buffering=1 (line buffered)
        log_file = open(log_path, 'a', encoding='utf-8', buffering=1)
        
        # Write header
        log_file.write(f"\n\n=== A8 Whisper Session Started: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        
        # Define a Tee-like writer if we want to keep original stdout (though it's None in noconsole)
        class LogWriter:
            def __init__(self, stream, file):
                self.stream = stream
                self.file = file
            def write(self, message):
                try:
                    self.file.write(message)
                    self.file.flush() # Ensure it hits disk
                    if self.stream: self.stream.write(message)
                except: pass
            def flush(self):
                try:
                    self.file.flush()
                    if self.stream: self.stream.flush()
                except: pass
                
        sys.stdout = LogWriter(sys.stdout, log_file)
        sys.stderr = LogWriter(sys.stderr, log_file)
        print(f"[INFO] Logging to {log_path}")
    except Exception as e:
        print(f"[ERROR] Failed to setup logging: {e}")
        pass # Fallback to no logging


from src import api_server

from src.webview_bridge import WebviewBridge

# Fix Encoding for Windows EXE (prevent UnicodeEncodeError)
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception as e:
        pass

# Fix High DPI for Windows
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

class DevServer:
    def __init__(self, host="localhost", port=5173, cwd="gui_web"):
        self.host = host
        self.port = port
        self.cwd = cwd
        self.process = None

    def is_running(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex((self.host, self.port)) == 0

    def start(self):
        if self.is_running():
            print(f"[OK] Vite server already running on {self.port}")
            return

        print(f"[INFO] Starting Vite server on port {self.port}...")
        # Use shell=True for Windows to find npm
        # IMPORTANT: Do not use PIPE for stdout/stderr if not reading them, 
        # otherwise buffer fills and process hangs.
        self.process = subprocess.Popen(
            "npm run dev", 
            shell=True, 
            cwd=self.cwd,
            # stdout=subprocess.DEVNULL, # Optional: Silence it
            # stderr=subprocess.DEVNULL
        )
        
        # Wait for port
        start_time = time.time()
        while time.time() - start_time < 30: # 30s timeout
            if self.is_running():
                print("\n[OK] Vite server is ready!")
                return
            
            elapsed = time.time() - start_time
            print(f"\r[WAIT] Waiting for Vite server... ({int(elapsed)}s)", end="", flush=True)
            time.sleep(0.5)
        
        print("\n[ERROR] Failed to start Vite server (Timeout). Check console for errors.")
        
        print("\n[ERROR] Failed to start Vite server.")
        
    def stop(self):
        if self.process:
            print("[INFO] Stopping Vite server...")
            # On Windows, killing the shell doesn't always kill the child
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.process.pid)])
            self.process = None

# Global reference for cleanup
overlay_process = None

def cleanup_processes():
    global overlay_process
    if overlay_process:
        print("Killing overlay process...")
        try:
            overlay_process.terminate()
            overlay_process.wait(timeout=1)
        except:
            try:
                overlay_process.kill()
            except:
                pass

def create_tray_icon(main_window):
    """Create system tray icon"""
    def show_window(icon, item):
        main_window.show()
        main_window.restore()

    def quit_app(icon, item):
        icon.stop()
        try:
            keyboard.unhook_all()
        except:
            pass
        
        # Cleanup overlay before exit
        cleanup_processes()
        
        main_window.destroy()
        os._exit(0)

    # Create "A8" Text Icon
    image = Image.new('RGB', (64, 64), color=(99, 102, 241)) # Original Blue
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, fall back to default
    try:
        from PIL import ImageFont
        try:
             # Segoe UI Bold usually available on Windows
             font = ImageFont.truetype("segoeui.ttf", 48) # Larger Font
        except:
             font = ImageFont.load_default()
    except:
        font = None
        
    text = "A8"
    # Centering (approximate for 64x64)
    draw.text((4, -2), text, fill=(255, 255, 255), font=font)
    
    menu = pystray.Menu(
        pystray.MenuItem('显示设置 / Show Settings', show_window, default=True),
        pystray.MenuItem('退出 / Quit', quit_app)
    )

    icon = pystray.Icon("A8 Whisper", image, "A8 Whisper", menu)
    return icon

def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller/Nuitka.
    """
    # Robust frozen detection for Nuitka
    is_frozen = getattr(sys, 'frozen', False) or "__compiled__" in globals()
    
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller (onefile/onedir)
        base_path = sys._MEIPASS
    elif is_frozen:
        # Nuitka Standalone
        # Resources are usually relative to the executable (sys.executable)
        base_path = os.path.dirname(sys.executable)
    else:
         # Development mode
         base_path = os.path.abspath(".")
             
    full_path = os.path.join(base_path, relative_path)
    return full_path

def main():
    # 0. Check for Overlay Mode (Subprocess)
    if "--overlay" in sys.argv:
        from src.run_overlay import main as start_overlay
        start_overlay()
        return

    global overlay_process
    api = WebviewBridge()
    
    # 1. Determine Environment
    is_frozen = getattr(sys, 'frozen', False) or "__compiled__" in globals()
    
    # Fallback: If running as a .exe that isn't python.exe, assume frozen (Nuitka Standalone often has this issue)
    if not is_frozen and sys.platform == "win32" and sys.executable.lower().endswith(".exe"):
        exe_name = os.path.basename(sys.executable).lower()
        if "python" not in exe_name:
            # print(f"[WARN] Nuitka detection fallback: Running as {exe_name}, assuming Frozen/Packaged mode.")
            is_frozen = True

    if is_frozen:
        # Running as packaged executable (Nuitka/PyInstaller)
        # Use get_resource_path to find the bundled gui_web/dist
        dist_dir = get_resource_path(os.path.join('gui_web', 'dist'))
        index_html = os.path.join(dist_dir, 'index.html')
        is_production = True
        print(f"[INFO] Running in Packaged Mode")
    else:
        # Running as script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        dist_dir = os.path.join(base_dir, '..', 'gui_web', 'dist')
        index_html = os.path.join(dist_dir, 'index.html')
        is_production = os.path.exists(index_html) and not os.environ.get("A8_DEV_MODE")
    
    server = None
    
    if is_production:
        # PRODUCTION MODE
        print("[INFO] Running in Production Mode (Local Files)")
        main_url = f"file://{index_html}"
    else:
        # DEVELOPMENT MODE
        print("[INFO] Running in Development Mode")
        gui_web_dir = os.path.join(base_dir, '..', 'gui_web')
        if not os.path.exists(gui_web_dir):
            print(f"[ERROR] gui_web directory not found at: {gui_web_dir}")
            print("[ERROR] Cannot start development server")
            return
            
        server = DevServer(cwd=gui_web_dir)
        server.start()
        atexit.register(server.stop)
        
        main_url = "http://localhost:5173"

    # Create Main Window (Settings)
    window_main = webview.create_window(
        'A8轻语', 
        url=main_url,
        js_api=api,
        width=1000,
        height=700,
        resizable=True,
        min_size=(800, 600),
        hidden=True,
        frameless=True,    # Remove Windows Title Bar
        easy_drag=False    # Disable global drag (fixes button clicks & resizing)
    )
    
    def init_app():
        # This runs in a separate thread AFTER the window loop has started
        # Safe to access window handle and start background tasks
        print("[OK] GUI Loop Started. Initializing App...")
        
        # 1. Initialize Bridge with Window Handle (Safe now)
        api._set_window_internal(window_main)
        # api.set_windows(window_main, None) # Old compatibility
        
        # 2. Start WebSocket API Server
        from src.api_server import start_server_wrapper
        threading.Thread(target=start_server_wrapper, daemon=True).start()
        
        # 3. Launch Overlay Process
        if is_frozen:
            overlay_cmd = [sys.executable, "--overlay"]
            print(f"[INFO] Launching Overlay (Frozen): {overlay_cmd}")
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            overlay_script = os.path.join(base_dir, 'run_overlay.py')
            overlay_cmd = [sys.executable, overlay_script]
            print(f"[INFO] Launching Overlay (Script): {overlay_script}")

        global overlay_process
        overlay_process = subprocess.Popen(
            overlay_cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            env=os.environ.copy()
        )
        
        # 4. Start Tray Icon
        tray = create_tray_icon(window_main)
        threading.Thread(target=tray.run, daemon=True).start()
        print("[OK] System Tray started")

    # Register cleanup on normal exit too
    atexit.register(cleanup_processes)

    # Start Pywebview Loop with Init Callback
    # Enable debug mode only in development
    debug_mode = os.environ.get("A8_DEV_MODE") == "1" or not getattr(sys, 'frozen', False)
    webview.start(func=init_app, debug=debug_mode)
    
    if server:
        server.stop()
        
    print("[INFO] App closing...")
    try:
        import keyboard
        keyboard.unhook_all()
    except:
        pass
    
    cleanup_processes()
    os._exit(0)

if __name__ == '__main__':
    main()

