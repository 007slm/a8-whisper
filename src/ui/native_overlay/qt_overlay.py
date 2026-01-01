import sys
import math
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, Signal, Slot
from PySide6.QtGui import (
    QPainter, QColor, QFont, QPainterPath, QPen, QBrush, 
    QLinearGradient, QRadialGradient
)

from .types import OverlayState, OverlayConfig

class ModernOverlay(QWidget):
    # Define signals for thread safety
    update_state_signal = Signal(object) # Using object to pass Enum
    update_level_signal = Signal(float)

    def __init__(self, config: OverlayConfig = None):
        super().__init__()
        self.config = config or OverlayConfig()
        
        # Window setup
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # State
        self._state = OverlayState.IDLE
        self._audio_level = 0.0
        self._phase = 0.0
        
        # Connect signals
        self.update_state_signal.connect(self._set_state_slot)
        self.update_level_signal.connect(self._update_level_slot)
        
        # Dimensions
        self._height = 48
        self._min_width = 160
        # self.setFixedSize(self._width, self._height) # Dynamic now
        self.resize(self._min_width, self._height)
        
        # Animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(16)  # 60 FPS
        
        # Font
        self._font = QFont("Segoe UI", 10)
        self._font.setWeight(QFont.DemiBold)

        # Initial Position
        self._force_position = False 
        self._center_on_screen()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = (geo.width() - self.width()) // 2
            # 16px from bottom of AVAILABLE geometry (usually sticks to taskbar top)
            y = geo.y() + geo.height() - self.height() - 16  
            self.move(x, y)

    def _update_size(self):
        # Get text for current state
        text_map = {
            OverlayState.RECORDING: "正在听...",
            OverlayState.RECOGNIZING: "识别中...",
            OverlayState.POLISHING: "润色中...",
            OverlayState.PROCESSING: "处理中..."
        }
        text = text_map.get(self._state, "")
        
        from PySide6.QtGui import QFontMetrics
        fm = QFontMetrics(self._font)
        text_w = fm.horizontalAdvance(text)
        
        # Layout: [15px] [Visualizer 30px] [10px] [Text] [20px]
        # Total width
        new_w = 15 + 30 + 10 + text_w + 20
        new_w = max(new_w, self._min_width)
        
        if self.width() != new_w:
            self.resize(new_w, self._height)
            self._center_on_screen() # Re-center when size changes

    # Public thread-safe methods
    def set_state(self, state: OverlayState):
        self.update_state_signal.emit(state)

    def update_audio_level(self, level: float):
        self.update_level_signal.emit(level)
        
    def destroy(self):
        self.close()

    @Slot(object)
    def _set_state_slot(self, state: OverlayState):
        if self._state == state:
            return
            
        print(f"Overlay State: {self._state} -> {state}")
        self._state = state
        self._update_size() # Update size based on new state/text
        
        if state == OverlayState.IDLE:
            self.hide()
        else:
            self.show()
            self.raise_()
            # Re-center if this is the first show or state change to ensure it's on top
            self._center_on_screen() 
            if not self.timer.isActive():
                self.timer.start(16)
        
        self.update()

    @Slot(float)
    def _update_level_slot(self, level: float):
        # Smooth interpolation: target level -> current level
        self._audio_level = self._audio_level * 0.7 + level * 0.3
        
    def _animate(self):
        self._phase += 0.15
        if self._phase > math.pi * 200: # Prevent overflow eventually
            self._phase = 0
        
        # Continuous repaint if visible
        if self.isVisible():
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. Draw Background (Pill Shape)
        rect = QRectF(0, 0, self.width(), self.height())
        path = QPainterPath()
        path.addRoundedRect(rect, 24, 24) 
        
        # Clear background for transparency
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.fillRect(rect, Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # Gradient Background (Semi-transparent)
        bg_gradient = QLinearGradient(0, 0, 0, self.height())
        bg_gradient.setColorAt(0.0, QColor(40, 40, 45, 240)) # Slightly more transparent
        bg_gradient.setColorAt(1.0, QColor(20, 20, 25, 240))
        
        painter.fillPath(path, bg_gradient)
        
        # Thin Border
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.drawPath(path)
        
        # 2. Draw Content
        # Layout: [15px] [Visualizer 30px] [10px] [Text] [20px]
        
        visualizer_area = QRectF(15, 0, 30, self.height())
        text_area = QRectF(55, 0, self.width() - 75, self.height())
        
        # Visualizer
        self._draw_visualizer(painter, visualizer_area)
        
        # Text
        text_map = {
            OverlayState.RECORDING: "正在听...",
            OverlayState.RECOGNIZING: "识别中...",
            OverlayState.POLISHING: "润色中...",
            OverlayState.PROCESSING: "处理中..."
        }
        text = text_map.get(self._state, "")
        
        painter.setPen(QColor(240, 240, 240))
        painter.setFont(self._font)
        # Left align text
        painter.drawText(text_area, Qt.AlignLeft | Qt.AlignVCenter, text)

    def _draw_visualizer(self, painter, rect):
        cx = rect.center().x()
        cy = rect.center().y()
        
        if self._state == OverlayState.RECORDING:
            # Dynamic Waveform (4 bars)
            bar_w = 3
            gap = 3
            n_bars = 4
            total_w = n_bars * bar_w + (n_bars - 1) * gap
            start_x = cx - total_w / 2
            
            for i in range(n_bars):
                # Phase shift for each bar
                off = i * 0.8
                # Sine wave pulsing
                val = math.sin(self._phase + off) * 0.5 + 0.5 # 0..1
                
                # Audio reactivity
                # Base height + audio boost
                h = 8 + (val * 6) + (self._audio_level * 18)
                h = min(h, 28) # Max height constraint
                
                x = start_x + i * (bar_w + gap)
                y = cy - h/2
                
                # Color Gradient for bars (Red/Orange)
                c = QColor("#FF453A") # Apple Red
                painter.setBrush(c)
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(QRectF(x, y, bar_w, h), 1.5, 1.5)
                
        elif self._state in [OverlayState.RECOGNIZING, OverlayState.PROCESSING, OverlayState.POLISHING]:
            # Spinner / Loader
            # Rotating Arc
            radius = 8
            angle = -math.degrees(self._phase) * 3
            
            pen = QPen(QColor("#0A84FF"), 2.5) # Apple Blue
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            
            painter.drawArc(
                QRectF(cx - radius, cy - radius, radius*2, radius*2),
                int(angle * 16),
                280 * 16 # 280 degree arc
            )

    def run(self):
        # Compatibility method: In Qt, we don't block here usually if we are a widget.
        # But looking at usage, this might be the entry point for the window thread.
        print("QtOverlay run called - verify QApplication exists")
        pass

# Helper to run in standalone mode or separate process
def run_overlay_process(config=None):
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    window = ModernOverlay(config)
    window.show()
    return app, window
