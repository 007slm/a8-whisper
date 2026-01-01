
# -*- coding: utf-8 -*-
import webview
import threading
import sys
import os

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

def main():
    # 0. Check for Overlay Mode (Subprocess)
    if "--overlay" in sys.argv:
        from src.run_overlay import main as start_overlay
        start_overlay()
        return

    global overlay_process
    api = WebviewBridge()
    
    # 1. Check for Production Build (dist/index.html)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # In packaged mode, check for gui_web/dist in the bundle
    if getattr(sys, 'frozen', False):
        # Running as packaged executable
        bundle_dir = sys._MEIPASS
        dist_dir = os.path.join(bundle_dir, 'gui_web', 'dist')
        index_html = os.path.join(dist_dir, 'index.html')
        is_production = True
    else:
        # Running as script
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
        if getattr(sys, 'frozen', False):
            overlay_cmd = [sys.executable, "--overlay"]
            print(f"[INFO] Launching Overlay (Frozen): {overlay_cmd}")
        else:
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
    webview.start(func=init_app, debug=True)
    
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

