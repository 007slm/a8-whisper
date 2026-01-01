import os
import sys
# from faster_whisper import WhisperModel # Lazy import

class ASREngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ASREngine, cls).__new__(cls)
            cls._instance.model = None
        return cls._instance

    def initialize(self, model_size="large-v3", device="cuda", compute_type="float16"):
        """
        Initialize the Faster-Whisper model.
        Prioritizes local models in ./models/faster-whisper-{size}
        """
        if self.model is not None:
            return

        from faster_whisper import WhisperModel
        print(f"Loading ASR Model: {model_size} on {device}...")
        
        # Robust path finding: Project Root / models
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Handle both development and packaged modes
        if getattr(sys, 'frozen', False):
            # Running as packaged executable
            project_root = os.path.dirname(sys.executable)
        else:
            # Running as script: src/core -> src -> root
            project_root = os.path.dirname(os.path.dirname(current_dir))
            
        local_path = os.path.join(project_root, "models", f"faster-whisper-{model_size}")
        
        print(f"[DEBUG] Current Dir: {current_dir}")
        print(f"[DEBUG] Project Root: {project_root}")
        print(f"[DEBUG] Checking Local Path: {local_path}")
        
        load_target = model_size # Default to name (auto-download to cache)
        
        is_local = False
        if os.path.exists(os.path.join(local_path, "config.json")):
            print(f"[OK] Found local model at: {local_path}")
            load_target = local_path
            is_local = True
        else:
            print(f"[WARN] Local model NOT found at {local_path}")
            print(f"[INFO] Will download from Hugging Face cache")

        try:
            self.model = WhisperModel(
                model_size_or_path=load_target,
                device=device,
                compute_type=compute_type,
                local_files_only=is_local # Prevent HF check if we have it
            )
            print("[OK] ASR Model Loaded Successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to load ASR Model: {e}")
            if device == "cuda":
                print("[INFO] Retrying with device='cpu'...")
                try:
                     self.model = WhisperModel(
                        model_size_or_path=load_target,
                        device="cpu",
                        compute_type="int8",
                        local_files_only=is_local
                    )
                     print("[OK] ASR Model Loaded Successfully (CPU Fallback).")
                except Exception as e2:
                    print(f"[ERROR] Failed to load ASR Model (CPU): {e2}")
                    raise e2
            else:
                 raise e

    def transcribe(self, audio_path, prompt=None):
        """
        Transcribe audio file.
        prompt: Optional initial prompt for context.
        """
        if not self.model:
            raise RuntimeError("ASR Model not initialized.")

        # Optimize for speed: beam_size=1 (greedy), language='zh' (skip detection)
        try:
             segments, info = self.model.transcribe(
                audio_path,
                beam_size=1,
                language="zh",
                initial_prompt=prompt
            )
             text = "".join([segment.text for segment in segments])
             return text.strip()
        except Exception as e:
            print(f"ASR Transcribe Error: {e}")
            if self.model.device == "cuda":
                 print("Critical: CUDA failed during transcription. Recommendation: Disable mismatched cuDNN or use CPU.")
                 raise e 
            raise e

# Global Instance
asr_engine = ASREngine()
