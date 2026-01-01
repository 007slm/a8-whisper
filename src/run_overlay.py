import sys
import os
from PySide6.QtWidgets import QApplication

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from src.ui.native_overlay.qt_overlay import ModernOverlay
from src.ui.native_overlay.manager import StateManager

def main():
    # Allow multiple instances or handle single instance check if needed
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    print("[INFO] Starting Native Overlay Process (PySide6)...")
    
    # Create Overlay Window
    overlay = ModernOverlay()
    
    # Initialize State Manager (connects to Main Process via WebSocket)
    state_manager = StateManager(overlay)
    state_manager.websocket_url = "ws://127.0.0.1:9000"
    
    print(f"Connecting to {state_manager.websocket_url}...")
    state_manager.connect_websocket()
    
    # Verify initial show
    # overlay.show()
    
    exit_code = app.exec()
    
    # Cleanup
    print("Overlay process exiting...")
    state_manager.disconnect_websocket()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
