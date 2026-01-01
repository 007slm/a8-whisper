"""
Window and state management for native overlay.
"""

import threading
import json
try:
    import websocket
except ImportError:
    # Fallback for testing or when websocket-client is not installed
    websocket = None
from typing import Optional, Callable, Dict, Any
import time

from .types import OverlayState, WebSocketMessage
from .qt_overlay import ModernOverlay


class StateManager:
    """State management and WebSocket communication"""
    
    def __init__(self, overlay_window: ModernOverlay):
        """Initialize state manager"""
        self.overlay_window = overlay_window
        self.websocket_client: Optional[websocket.WebSocket] = None
        self.websocket_url = "ws://localhost:9000"  # Updated to match API server port
        
        # Threading
        self._ws_thread: Optional[threading.Thread] = None
        self._running = False
        self._reconnect_delay = 1.0
        self._max_reconnect_delay = 30.0
        
        # Callbacks
        self._message_handlers: Dict[str, Callable] = {
            "app_state": self._handle_state_message,
            "audio_level": self._handle_audio_level_message,
            "init_status": lambda m: None  # Ignore init status messages
        }
        
    def connect_websocket(self) -> None:
        """Connect to WebSocket server"""
        if self._running:
            return
            
        self._running = True
        self._ws_thread = threading.Thread(
            target=self._websocket_loop,
            daemon=True
        )
        self._ws_thread.start()
        
    def disconnect_websocket(self) -> None:
        """Disconnect from WebSocket server"""
        self._running = False
        
        if self.websocket_client:
            try:
                self.websocket_client.close()
            except Exception:
                pass
            self.websocket_client = None
            
        if self._ws_thread and self._ws_thread.is_alive():
            self._ws_thread.join(timeout=2.0)
            
    def _websocket_loop(self) -> None:
        """Main WebSocket connection loop with reconnection"""
        if websocket is None:
            print("WebSocket client not available - install websocket-client package")
            return
            
        reconnect_delay = self._reconnect_delay
        
        while self._running:
            try:
                print(f"Connecting to WebSocket: {self.websocket_url}")
                
                self.websocket_client = websocket.WebSocket()
                self.websocket_client.connect(self.websocket_url)
                
                print("WebSocket connected")
                reconnect_delay = self._reconnect_delay  # Reset delay on successful connection
                
                # Message loop
                while self._running:
                    try:
                        message = self.websocket_client.recv()
                        if message:
                            self._process_message(message)
                    except Exception as e:
                        # Handle both websocket exceptions and general exceptions
                        if websocket and hasattr(websocket, 'WebSocketTimeoutException') and isinstance(e, websocket.WebSocketTimeoutException):
                            continue
                        print(f"WebSocket receive error: {e}")
                        break
                        
            except Exception as e:
                print(f"WebSocket connection error: {e}")
                
            finally:
                if self.websocket_client:
                    try:
                        self.websocket_client.close()
                    except Exception:
                        pass
                    self.websocket_client = None
                    
            # Reconnection delay with exponential backoff
            if self._running:
                print(f"Reconnecting in {reconnect_delay} seconds...")
                time.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, self._max_reconnect_delay)
                
    def _process_message(self, message_str: str) -> None:
        """Process incoming WebSocket message"""
        try:
            data = json.loads(message_str)
            message = WebSocketMessage.from_dict(data)
            
            handler = self._message_handlers.get(message.type)
            if handler:
                handler(message)
            else:
                print(f"Unknown message type: {message.type}")
                
        except json.JSONDecodeError as e:
            print(f"Invalid JSON message: {e}")
        except Exception as e:
            print(f"Error processing message: {e}")
            
    def _handle_state_message(self, message: WebSocketMessage) -> None:
        """Handle app state change messages"""
        try:
            state_str = message.data
            if isinstance(state_str, str):
                state = OverlayState(state_str)
                self.overlay_window.set_state(state)
            else:
                print(f"Invalid state data: {message.data}")
        except ValueError as e:
            print(f"Invalid state value: {message.data}, error: {e}")
            
    def _handle_audio_level_message(self, message: WebSocketMessage) -> None:
        """Handle audio level update messages"""
        try:
            level = float(message.data)
            self.overlay_window.update_audio_level(level)
        except (ValueError, TypeError) as e:
            print(f"Invalid audio level: {message.data}, error: {e}")
            
    def send_message(self, message_type: str, data: Any) -> None:
        """Send message to WebSocket server"""
        if not self.websocket_client:
            return
            
        try:
            message = WebSocketMessage(type=message_type, data=data)
            message_str = json.dumps(message.to_dict())
            self.websocket_client.send(message_str)
        except Exception as e:
            print(f"Error sending message: {e}")
            
    def add_message_handler(self, message_type: str, handler: Callable) -> None:
        """Add custom message handler"""
        self._message_handlers[message_type] = handler
        
    def remove_message_handler(self, message_type: str) -> None:
        """Remove message handler"""
        if message_type in self._message_handlers:
            del self._message_handlers[message_type]