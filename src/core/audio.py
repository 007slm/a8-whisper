# import sounddevice as sd # Lazy import
import numpy as np
import wave
import tempfile
import threading
import os
import time

class AudioRecorder:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.recording = False
        self.audio_data = []
        self.stream = None
        self.start_time = 0

    def start(self):
        """Start recording from default microphone."""
        import sounddevice as sd
        if self.recording:
            return

        self.recording = True
        self.audio_data = [] # Reset buffer
        self.start_time = time.time()
        
        def callback(indata, frames, time, status):
            if status:
                print(status, flush=True)
            if self.recording:
                self.audio_data.append(indata.copy())

        # Start stream
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='int16',
            callback=callback
        )
        self.stream.start()
        print("Recording started...")

    def stop(self):
        """Stop recording and save to temporary file. Returns file path."""
        if not self.recording:
            return None

        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        print("Recording stopped.")
        
        if not self.audio_data:
            return None

        # Concatenate and save
        audio_np = np.concatenate(self.audio_data, axis=0)
        
        # Create temp file
        temp_dir = os.path.join(tempfile.gettempdir(), "a8wisper")
        os.makedirs(temp_dir, exist_ok=True)
        filename = os.path.join(temp_dir, f"rec_{int(time.time())}.wav")
        
        # Save using wave module
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2) # 16-bit = 2 bytes
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_np.tobytes())
            
        return filename

    def get_amplitude(self):
        """Get current amplitude for visualization (approx)."""
        if self.recording and self.audio_data:
            # Get latest chunk
            last_chunk = self.audio_data[-1]
            # RMS amplitude
            # Check for empty chunk to avoid warning
            if len(last_chunk) > 0:
                rms = np.sqrt(np.mean(last_chunk**2))
                return float(rms)
        return 0.0
