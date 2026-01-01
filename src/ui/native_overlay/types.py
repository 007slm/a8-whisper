"""
Data models and type definitions for the native overlay system.
"""

from dataclasses import dataclass
from typing import Dict, Any
from enum import Enum


class OverlayState(Enum):
    """Overlay state enumeration"""
    IDLE = "IDLE"
    RECORDING = "RECORDING"
    RECOGNIZING = "RECOGNIZING"
    POLISHING = "POLISHING"
    PROCESSING = "PROCESSING"


@dataclass
class OverlayConfig:
    """Overlay configuration data model"""
    enabled: bool = True
    position: str = "bottom_center"
    size: Dict[str, int] = None
    opacity: float = 0.95
    animation_fps: int = 30
    colors: Dict[str, str] = None
    
    def __post_init__(self):
        if self.size is None:
            self.size = {"width": 180, "height": 44}
        if self.colors is None:
            self.colors = {
                "recording": "#EF4444",    # Red
                "recognizing": "#3B82F6",  # Blue  
                "polishing": "#8B5CF6",    # Purple
                "processing": "#FFFFFF"    # White
            }


@dataclass
class WebSocketMessage:
    """WebSocket message data model"""
    type: str
    data: Any
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebSocketMessage':
        """Create WebSocketMessage from dictionary"""
        return cls(
            type=data.get("type", ""),
            data=data.get("data")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "type": self.type,
            "data": self.data
        }
