"""
Animation utilities for the SAT Question Bank application.
Provides reusable animation components and effects for UI interactions.
"""
import logging
from enum import Enum
from typing import Any, Callable, Optional, Union

from PyQt6.QtCore import (
    QEasingCurve, QObject, QPoint, QPropertyAnimation, QRect, 
    QTimer, Qt, QParallelAnimationGroup, QSequentialAnimationGroup,
    QPointF, pyqtProperty, pyqtSignal
)
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QLabel, QWidget, QGraphicsOpacityEffect, QPushButton, 
    QProgressBar, QApplication, QFrame, QLineEdit, QHBoxLayout
)


class AnimationSpeed(Enum):
    """Standard animation durations for consistency."""
    VERY_FAST = 100
    FAST = 150
    NORMAL = 300
    SLOW = 500
    VERY_SLOW = 800


class AnimationService:
    """
    Service for creating and managing animations throughout the application.
    
    Provides standardized methods for common animation types like property 
    animations, fade effects, shake effects, and highlight effects.
    """
    
    def __init__(self):
        """Initialize the animation service."""
        self.logger = logging.getLogger(__name__)
        
    def create_property_animation(
        self, 
        target: QObject, 
        property_name: str, 
        start_value: Any, 
        end_value: Any, 
        duration: int = AnimationSpeed.NORMAL.value, 
        easing_curve: QEasingCurve.Type = QEasingCurve.Type.OutCubic,
        finished_callback: Optional[Callable] = None
    ) -> QPropertyAnimation:
        """
        Create a property animation for the target object.
        
        Args:
            target: Object to animate
            property_name: Name of the property to animate (e.g., "geometry", "pos")
            start_value: Starting value of the property
            end_value: Ending value of the property
            duration: Duration of the animation in milliseconds
            easing_curve: Easing curve to use for the animation
            finished_callback: Optional callback function to call when animation finishes
            
        Returns:
            The created property animation
        """
        animation = QPropertyAnimation(target, property_name.encode())
        animation.setStartValue(start_value)
        animation.setEndValue(end_value)
        animation.setDuration(duration)
        animation.setEasingCurve(easing_curve)
        
        if finished_callback:
            animation.finished.connect(finished_callback)
            
        return animation
    
    def create_fade_animation(
        self, 
        widget: QWidget, 
        start_opacity: float = 0.0, 
        end_opacity: float = 1.0, 
        duration: int = AnimationSpeed.NORMAL.value,
        finished_callback: Optional[Callable] = None,
        auto_start: bool = False
    ) -> QPropertyAnimation:
        """
        Create a fade animation for the widget.
        
        Args:
            widget: Widget to animate
            start_opacity: Starting opacity (0.0 to 1.0)
            end_opacity: Ending opacity (0.0 to 1.0)
            duration: Duration of the animation in milliseconds
            finished_callback: Optional callback function to call when animation finishes
            auto_start: Whether to start the animation immediately
            
        Returns:
            The created property animation
        """
        # Create opacity effect if it doesn't exist
        opacity_effect = widget.graphicsEffect()
        if not isinstance(opacity_effect, QGraphicsOpacityEffect):
            opacity_effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(opacity_effect)
        
        # Make sure widget is visible if fading in
        if start_opacity == 0.0 and end_opacity > 0.0:
            widget.show()
        
        # Set initial opacity
        opacity_effect.setOpacity(start_opacity)
        
        # Create the animation
        animation = self.create_property_animation(
            opacity_effect, "opacity", start_opacity, end_opacity, 
            duration, QEasingCurve.Type.InOutCubic, finished_callback
        )
        
        # Connect a callback to hide the widget if fading out completely
        if end_opacity == 0.0:
            animation.finished.connect(lambda: widget.hide())
        
        if auto_start:
            animation.start()
            
        return animation
    
    def create_shake_animation(
        self, 
        widget: QWidget, 
        distance: int = 5, 
        duration: int = AnimationSpeed.FAST.value,
        finished_callback: Optional[Callable] = None,
        auto_start: bool = False
    ) -> QSequentialAnimationGroup:
        """
        Create a horizontal shake animation for the widget.
        
        Args:
            widget: Widget to animate
            distance: Distance to shake in pixels
            duration: Duration of the animation in milliseconds
            finished_callback: Optional callback function to call when animation finishes
            auto_start: Whether to start the animation immediately
            
        Returns:
            The created sequential animation group
        """
        # Get the original position
        original_pos = widget.pos()
        
        # Create sequential animation group for the shake motion
        shake_group = QSequentialAnimationGroup()
        
        # Create animations for each direction
        # Right
        right_anim = self.create_property_animation(
            widget, "pos", 
            original_pos, 
            QPoint(original_pos.x() + distance, original_pos.y()),
            duration // 5
        )
        # Left
        left_anim = self.create_property_animation(
            widget, "pos", 
            QPoint(original_pos.x() + distance, original_pos.y()),
            QPoint(original_pos.x() - distance, original_pos.y()),
            duration // 5
        )
        # Middle
        middle_anim = self.create_property_animation(
            widget, "pos", 
            QPoint(original_pos.x() - distance, original_pos.y()),
            QPoint(original_pos.x() + distance // 2, original_pos.y()),
            duration // 5
        )
        # Right small
        right_small_anim = self.create_property_animation(
            widget, "pos", 
            QPoint(original_pos.x() + distance // 2, original_pos.y()),
            QPoint(original_pos.x() - distance // 2, original_pos.y()),
            duration // 5
        )
        # Back to original
        original_anim = self.create_property_animation(
            widget, "pos", 
            QPoint(original_pos.x() - distance // 2, original_pos.y()),
            original_pos,
            duration // 5
        )
        
        # Add animations to the group
        shake_group.addAnimation(right_anim)
        shake_group.addAnimation(left_anim)
        shake_group.addAnimation(middle_anim)
        shake_group.addAnimation(right_small_anim)
        shake_group.addAnimation(original_anim)
        
        if finished_callback:
            shake_group.finished.connect(finished_callback)
            
        if auto_start:
            shake_group.start()
            
        return shake_group
    
    def create_highlight_animation(
        self, 
        widget: QWidget, 
        start_color: QColor, 
        end_color: QColor, 
        flash_color: Optional[QColor] = None,
        duration: int = AnimationSpeed.NORMAL.value,
        property_name: str = "background-color",
        finished_callback: Optional[Callable] = None,
        auto_start: bool = False
    ) -> QSequentialAnimationGroup:
        """
        Create a highlight (flash) animation for the widget's stylesheet property.
        
        Args:
            widget: Widget to animate
            start_color: Starting color
            end_color: Ending color
            flash_color: Optional color for the "flash" middle state
            duration: Duration of the animation in milliseconds
            property_name: Stylesheet property to animate (e.g., "background-color", "color")
            finished_callback: Optional callback function to call when animation finishes
            auto_start: Whether to start the animation immediately
            
        Returns:
            The created sequential animation group
        """
        # Create the sequential animation group
        highlight_group = QSequentialAnimationGroup()
        
        # Set the initial stylesheet
        widget.setStyleSheet(f"{widget.__class__.__name__} {{ {property_name}: {start_color.name()}; }}")
        
        # If flash color is provided, create a three-step animation
        if flash_color:
            # First animation to flash color
            flash_duration = duration // 3
            
            # Flash animation (start to flash)
            def update_style_to_flash():
                widget.setStyleSheet(f"{widget.__class__.__name__} {{ {property_name}: {flash_color.name()}; }}")
            
            timer1 = QTimer(widget)
            timer1.setSingleShot(True)
            timer1.timeout.connect(update_style_to_flash)
            timer1.start(flash_duration)
            
            # Return animation (flash to end)
            def update_style_to_end():
                widget.setStyleSheet(f"{widget.__class__.__name__} {{ {property_name}: {end_color.name()}; }}")
                
            timer2 = QTimer(widget)
            timer2.setSingleShot(True)
            timer2.timeout.connect(update_style_to_end)
            timer2.start(flash_duration * 2)
        else:
            # Simple animation from start to end color
            def update_style_to_end():
                widget.setStyleSheet(f"{widget.__class__.__name__} {{ {property_name}: {end_color.name()}; }}")
                
            timer = QTimer(widget)
            timer.setSingleShot(True)
            timer.timeout.connect(update_style_to_end)
            timer.start(duration)
        
        if finished_callback:
            # Create a timer for the callback
            callback_timer = QTimer(widget)
            callback_timer.setSingleShot(True)
            callback_timer.timeout.connect(finished_callback)
            callback_timer.start(duration)
            
        return highlight_group


class PulsatingButton(QPushButton):
    """
    Button with a pulsating animation effect.
    
    Creates a button that pulses to draw attention when highlighted.
    """
    
    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        """
        Initialize the pulsating button.
        
        Args:
            text: Button text
            parent: Parent widget
        """
        super().__init__(text, parent)
        self._scale = 1.0
        self._pulsating = False
        self._animation = QPropertyAnimation(self, b"scale")
        self._animation.setDuration(800)
        self._animation.setLoopCount(-1)  # Infinite loop
        self._animation.setStartValue(1.0)
        self._animation.setEndValue(1.1)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Connect animation change to update
        self._animation.valueChanged.connect(self.update)
    
    @pyqtProperty(float)
    def scale(self) -> float:
        return self._scale
    
    @scale.setter
    def scale(self, value: float):
        self._scale = value
        self.update()
    
    def set_pulsating(self, enabled: bool):
        """
        Enable or disable the pulsating effect.
        
        Args:
            enabled: Whether the pulsating effect is enabled
        """
        if enabled == self._pulsating:
            return
            
        self._pulsating = enabled
        if enabled:
            self._animation.start()
        else:
            self._animation.stop()
            self._scale = 1.0
            self.update()
    
    def paintEvent(self, event):
        """
        Override the paint event to apply the scale effect.
        
        Args:
            event: Paint event
        """
        # Import QPainter here to avoid circular imports
        from PyQt6.QtGui import QPainter
        
        if self._pulsating and self._scale != 1.0:
            # Save painter state
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Apply scaling transformation
            painter.translate(self.width() / 2, self.height() / 2)
            painter.scale(self._scale, self._scale)
            painter.translate(-self.width() / 2, -self.height() / 2)
            
            # Let the QPushButton paint itself
            super().paintEvent(event)
            
            # Restore painter state
            painter.end()
        else:
            super().paintEvent(event)


class ToastNotification(QFrame):
    """
    Toast notification widget that appears temporarily and fades out.
    
    Displays a short message that appears and disappears automatically.
    """
    
    closed = pyqtSignal()
    
    def __init__(self, 
                 parent: QWidget, 
                 message: str, 
                 duration: int = 3000,
                 position: str = "bottom",
                 icon: Optional[str] = None):
        """
        Initialize the toast notification.
        
        Args:
            parent: Parent widget
            message: Message to display
            duration: Duration to show the toast in milliseconds
            position: Position to show the toast ("top", "bottom", "center")
            icon: Optional icon to display
        """
        super().__init__(parent)
        
        # Set up appearance
        self.setObjectName("ToastNotification")
        self.setStyleSheet("""
            #ToastNotification {
                background-color: rgba(60, 60, 60, 220);
                border-radius: 6px;
                color: white;
                padding: 10px 15px;
            }
        """)
        
        # Import QIcon here to avoid circular imports
        from PyQt6.QtGui import QIcon
        
        # Set up layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # Add icon if provided
        if icon:
            self.icon_label = QLabel()
            self.icon_label.setPixmap(QIcon(icon).pixmap(24, 24))
            self.layout.addWidget(self.icon_label)
        
        # Add message label
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.message_label)
        
        # Set size
        self.adjustSize()
        
        # Position the toast
        self._position = position
        self._position_toast()
        
        # Create opacity effect for fade-in/fade-out
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self.opacity_effect)
        
        # Initialize animations
        self.animation_service = AnimationService()
        self.fade_in = self.animation_service.create_property_animation(
            self.opacity_effect, "opacity", 0.0, 1.0, 300, QEasingCurve.Type.OutCubic
        )
        
        self.fade_out = self.animation_service.create_property_animation(
            self.opacity_effect, "opacity", 1.0, 0.0, 500, QEasingCurve.Type.InCubic,
            self._on_fade_out_finished
        )
        
        # Set up timer for auto-close
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.close_toast)
        
        # Start showing
        self.show()
        self.fade_in.start()
        self.timer.start(duration)
    
    def _position_toast(self):
        """Position the toast based on the specified position."""
        parent_rect = self.parent().rect()
        toast_width = self.width()
        toast_height = self.height()
        
        # Calculate position
        if self._position == "top":
            pos_x = (parent_rect.width() - toast_width) // 2
            pos_y = 20
        elif self._position == "center":
            pos_x = (parent_rect.width() - toast_width) // 2
            pos_y = (parent_rect.height() - toast_height) // 2
        else:  # bottom
            pos_x = (parent_rect.width() - toast_width) // 2
            pos_y = parent_rect.height() - toast_height - 20
        
        # Set position
        self.move(pos_x, pos_y)
    
    def close_toast(self):
        """Start the fade-out animation to close the toast."""
        self.timer.stop()
        self.fade_out.start()
    
    def _on_fade_out_finished(self):
        """Handle the fade-out animation finishing."""
        self.closed.emit()
        self.deleteLater()


class ValidationAnimator:
    """
    Animator for form validation effects.
    
    Provides animations for highlighting valid/invalid form fields.
    """
    
    def __init__(self):
        """Initialize the validation animator."""
        self.animation_service = AnimationService()
        self.logger = logging.getLogger(__name__)
    
    def highlight_invalid_field(self, 
                               field: QWidget, 
                               message: Optional[str] = None,
                               parent: Optional[QWidget] = None):
        """
        Highlight an invalid field with a shake animation and red border.
        
        Args:
            field: The field to highlight
            message: Optional validation message to display
            parent: Optional parent widget for the validation message
        """
        # Original style to revert to later
        original_style = field.styleSheet()
        
        # Highlight with red border
        field.setStyleSheet(original_style + """
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                border: 2px solid #F44336;
                background-color: #FFEBEE;
            }
        """)
        
        # Create and start shake animation
        shake_anim = self.animation_service.create_shake_animation(
            field, 5, AnimationSpeed.FAST.value, auto_start=True
        )
        
        # Reset style after animation
        def reset_style():
            # Don't completely reset - keep a subtle red border
            field.setStyleSheet(original_style + """
                QLineEdit, QTextEdit, QComboBox, QSpinBox {
                    border: 1px solid #F44336;
                }
            """)
            
        shake_anim.finished.connect(reset_style)
        
        # Show validation message if provided
        if message and parent:
            error_label = QLabel(message, parent)
            error_label.setStyleSheet("color: #F44336; font-size: 11px;")
            error_label.setObjectName("ValidationMessage")
            
            # Position below the field
            pos = field.mapTo(parent, QPoint(0, field.height()))
            error_label.move(pos.x(), pos.y() + 2)
            
            # Show with fade-in animation
            error_label.setGraphicsEffect(QGraphicsOpacityEffect(error_label))
            error_label.graphicsEffect().setOpacity(0)
            error_label.show()
            
            # Create fade-in animation
            fade_in = self.animation_service.create_fade_animation(
                error_label, 0.0, 1.0, AnimationSpeed.FAST.value, auto_start=True
            )
            
            # Remove previous error message if exists
            for child in parent.children():
                if child is not error_label and child.objectName() == "ValidationMessage":
                    child.deleteLater()
    
    def highlight_valid_field(self, field: QWidget):
        """
        Highlight a valid field with a brief green border.
        
        Args:
            field: The field to highlight
        """
        # Original style to revert to later
        original_style = field.styleSheet()
        
        # Highlight with green border
        field.setStyleSheet(original_style + """
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                border: 2px solid #4CAF50;
                background-color: #E8F5E9;
            }
        """)
        
        # Reset style after a delay
        QTimer.singleShot(1000, lambda: field.setStyleSheet(original_style))
    
    def clear_validation_state(self, field: QWidget, parent: Optional[QWidget] = None):
        """
        Clear validation effects from a field.
        
        Args:
            field: The field to clear validation state from
            parent: Optional parent widget for finding validation messages
        """
        # Reset field style
        field.setStyleSheet(field.styleSheet().replace(
            """
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                border: 1px solid #F44336;
            }
            """, "").replace(
            """
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                border: 2px solid #F44336;
                background-color: #FFEBEE;
            }
            """, "").replace(
            """
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                border: 2px solid #4CAF50;
                background-color: #E8F5E9;
            }
            """, "")
        )
        
        # Remove any validation messages
        if parent:
            for child in parent.children():
                if (child.objectName() == "ValidationMessage" and 
                    child.geometry().y() > field.mapTo(parent, QPoint(0, field.height())).y()):
                    # Fade out and remove
                    fade_out = self.animation_service.create_fade_animation(
                        child, 1.0, 0.0, AnimationSpeed.FAST.value, 
                        lambda: child.deleteLater(), auto_start=True
                    )


class ProgressAnimator:
    """
    Animator for progress indicators and loading effects.
    
    Provides animations for progress bars, spinners, and loading indicators.
    """
    
    def __init__(self):
        """Initialize the progress animator."""
        self.animation_service = AnimationService()
        self.logger = logging.getLogger(__name__)
    
    def animate_progress_bar(self, 
                           progress_bar: QProgressBar, 
                           start_value: int = 0,
                           end_value: int = 100,
                           duration: int = AnimationSpeed.SLOW.value,
                           easing_curve: QEasingCurve.Type = QEasingCurve.Type.OutCubic):
        """
        Animate a progress bar from start to end value.
        
        Args:
            progress_bar: The progress bar to animate
            start_value: Starting value
            end_value: Ending value
            duration: Animation duration in milliseconds
            easing_curve: Easing curve for the animation
        """
        # Reset to start value
        progress_bar.setValue(start_value)
        
        # Create the animation
        animation = self.animation_service.create_property_animation(
            progress_bar, "value", start_value, end_value, 
            duration, easing_curve
        )
        
        # Start the animation
        animation.start()
        
        return animation
    
    def create_pulsating_progress_bar(self, 
                                   progress_bar: QProgressBar,
                                   min_value: int = 0,
                                   max_value: int = 100):
        """
        Create a pulsating effect for a progress bar (for indeterminate progress).
        
        Args:
            progress_bar: The progress bar to animate
            min_value: Minimum pulsating value
            max_value: Maximum pulsating value
        """
        # Set up progress bar for indeterminate mode
        progress_bar.setRange(min_value, max_value)
        progress_bar.setValue(min_value)
        
        # Create forward animation
        forward_anim = self.animation_service.create_property_animation(
            progress_bar, "value", min_value, max_value, 
            AnimationSpeed.SLOW.value, QEasingCurve.Type.InOutSine
        )
        
        # Create backward animation
        backward_anim = self.animation_service.create_property_animation(
            progress_bar, "value", max_value, min_value, 
            AnimationSpeed.SLOW.value, QEasingCurve.Type.InOutSine
        )
        
        # Create sequential animation group
        group = QSequentialAnimationGroup()
        group.addAnimation(forward_anim)
        group.addAnimation(backward_anim)
        group.setLoopCount(-1)  # Infinite loop
        
        # Start the animation
        group.start()
        
        return group
    
    def create_button_loading_state(self, 
                                 button: QPushButton, 
                                 loading_text: str = "Loading...",
                                 original_text: Optional[str] = None):
        """
        Create a loading state for a button.
        
        Args:
            button: The button to animate
            loading_text: Text to display while loading
            original_text: Original button text (if not provided, current text is used)
            
        Returns:
            A tuple containing (original_text, original_enabled, animation)
        """
        # Store original state
        original_text = original_text or button.text()
        original_enabled = button.isEnabled()
        
        # Set loading state
        button.setText(loading_text)
        button.setEnabled(False)
        
        # Add ellipsis animation
        dots = 0
        
        def update_dots():
            nonlocal dots
            dots = (dots + 1) % 4
            button.setText(loading_text.rstrip('.') + '.' * dots)
        
        # Create timer for ellipsis animation
        timer = QTimer(button)
        timer.timeout.connect(update_dots)
        timer.start(300)
        
        # Return original state information and timer
        return (original_text, original_enabled, timer)
    
    def restore_button_state(self, 
                           button: QPushButton, 
                           original_state: tuple):
        """
        Restore a button from loading state.
        
        Args:
            button: The button to restore
            original_state: Tuple returned from create_button_loading_state
        """
        original_text, original_enabled, timer = original_state
        
        # Stop the timer
        timer.stop()
        
        # Restore original state
        button.setText(original_text)
        button.setEnabled(original_enabled)


class NotificationManager:
    """
    Manager for displaying temporary notifications.
    
    Provides methods for showing toast messages, status bar updates,
    and other notification types.
    """
    
    def __init__(self, status_bar=None):
        """
        Initialize the notification manager.
        
        Args:
            status_bar: Optional status bar for showing status messages
        """
        self.animation_service = AnimationService()
        self.logger = logging.getLogger(__name__)
        self.status_bar = status_bar
        self.active_toasts = []
    
    def show_toast(self, 
                  message: str, 
                  parent: QWidget,
                  duration: int = 3000,
                  position: str = "bottom",
                  icon: Optional[str] = None):
        """
        Show a toast notification.
        
        Args:
            message: Message to display
            parent: Parent widget
            duration: Duration to show the toast in milliseconds
            position: Position to show the toast ("top", "bottom", "center")
            icon: Optional icon to display
            
        Returns:
            The created toast notification
        """
        toast = ToastNotification(parent, message, duration, position, icon)
        toast.closed.connect(lambda: self.active_toasts.remove(toast) if toast in self.active_toasts else None)
        self.active_toasts.append(toast)
        return toast
    
    def show_status_message(self, 
                          message: str, 
                          duration: int = 3000,
                          fade: bool = True):
        """
        Show a temporary message in the status bar.
        
        Args:
            message: Message to display
            duration: Duration to show the message in milliseconds
            fade: Whether to fade the message in/out
        """
        if not self.status_bar:
            self.logger.warning("No status bar available for status message")
            return
        
        # Show the message
        self.status_bar.showMessage(message)
        
        # Create a timer to clear the message
        QTimer.singleShot(duration, lambda: self.status_bar.showMessage("Ready"))
    
    def pulse_status_message(self, 
                           message: str, 
                           pulse_count: int = 3,
                           pulse_duration: int = 300):
        """
        Show a pulsing status message with highlighted background.
        
        Args:
            message: Message to display
            pulse_count: Number of pulses
            pulse_duration: Duration of each pulse in milliseconds
        """
        if not self.status_bar:
            self.logger.warning("No status bar available for status message")
            return
        
        # Original stylesheet
        original_style = self.status_bar.styleSheet()
        
        # Counter for pulses
        pulses_left = pulse_count * 2  # Each complete pulse is two states (highlight and normal)
        
        # Show the message initially
        self.status_bar.showMessage(message)
        
        def pulse_step():
            nonlocal pulses_left
            pulses_left -= 1
            
            # Toggle between highlighted and normal state
            if pulses_left % 2 == 1:
                # Highlight
                self.status_bar.setStyleSheet(original_style + """
                    QStatusBar {
                        background-color: #2196F3;
                        color: white;
                    }
                """)
            else:
                # Normal
                self.status_bar.setStyleSheet(original_style)
            
            # Continue pulsing if there are pulses left
            if pulses_left > 0:
                QTimer.singleShot(pulse_duration, pulse_step)
        
        # Start the pulsing
        pulse_step()
    
    def show_success_indicator(self, 
                             widget: QWidget, 
                             duration: int = 1000):
        """
        Show a success indicator on a widget.
        
        Args:
            widget: Widget to show the indicator on
            duration: Duration to show the indicator in milliseconds
        """
        # Original stylesheet
        original_style = widget.styleSheet()
        
        # Apply success style
        widget.setStyleSheet(original_style + """
            QWidget {
                border: 2px solid #4CAF50 !important;
                background-color: #E8F5E9 !important;
            }
        """)
        
        # Reset after duration
        QTimer.singleShot(duration, lambda: widget.setStyleSheet(original_style))
    
    def show_error_indicator(self, 
                           widget: QWidget, 
                           duration: int = 1000):
        """
        Show an error indicator on a widget.
        
        Args:
            widget: Widget to show the indicator on
            duration: Duration to show the indicator in milliseconds
        """
        # Original stylesheet
        original_style = widget.styleSheet()
        
        # Apply error style
        widget.setStyleSheet(original_style + """
            QWidget {
                border: 2px solid #F44336 !important;
                background-color: #FFEBEE !important;
            }
        """)
        
        # Reset after duration
        QTimer.singleShot(duration, lambda: widget.setStyleSheet(original_style))