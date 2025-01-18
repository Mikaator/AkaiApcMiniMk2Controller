from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication

class Theme:
    # Farbpaletten
    DARK = {
        'bg': '#1e1e1e',
        'surface': '#252526',
        'primary': '#007acc',
        'text': '#ffffff',
        'text_secondary': '#cccccc',
        'border': '#333333',
        'hover': '#2a2d2e',
        'pressed': '#094771',
        'accent': '#0098ff'
    }
    
    LIGHT = {
        'bg': '#ffffff',
        'surface': '#f3f3f3',
        'primary': '#0078d4',
        'text': '#000000',
        'text_secondary': '#616161',
        'border': '#e0e0e0',
        'hover': '#f5f5f5',
        'pressed': '#c7e0f4',
        'accent': '#106ebe'
    }

    @staticmethod
    def set_dark_theme(app: QApplication):
        colors = Theme.DARK
        app.setStyleSheet(f"""
            QMainWindow, QDialog {{
                background-color: {colors['bg']};
                min-width: 600px;
                min-height: 400px;
            }}
            
            QWidget {{
                color: {colors['text']};
                font-family: Segoe UI, Arial;
                font-size: 11px;
            }}
            
            QGroupBox {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: 6px;
                margin-top: 8px;
                padding: 8px;
                font-weight: bold;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
                color: {colors['text_secondary']};
            }}
            
            QPushButton {{
                background-color: {colors['primary']};
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                color: white;
                font-weight: bold;
                min-height: 18px;
            }}
            
            QPushButton:hover {{
                background-color: {colors['accent']};
            }}
            
            QPushButton:pressed {{
                background-color: {colors['pressed']};
            }}
            
            QPushButton:checked {{
                background-color: {colors['pressed']};
            }}
            
            QComboBox {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: 4px;
                padding: 2px 4px;
                min-height: 18px;
                min-width: 100px;
            }}
            
            QComboBox:hover {{
                border-color: {colors['primary']};
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                color: {colors['text']};
                selection-background-color: {colors['primary']};
                selection-color: white;
                padding: 2px;
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 18px;
            }}
            
            QComboBox::down-arrow {{
                width: 10px;
                height: 10px;
                margin-right: 4px;
            }}
            
            QFrame {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: 6px;
            }}
            
            QLabel {{
                color: {colors['text_secondary']};
                min-height: 14px;
            }}
            
            QHBoxLayout {{
                spacing: 4px;
            }}
            
            QVBoxLayout {{
                spacing: 4px;
            }}
            
            QToolBar {{
                background: transparent;
                border: none;
            }}
            
            QToolBar QPushButton {{
                background: transparent;
                border-radius: 15px;
                padding: 4px;
            }}
            
            QToolBar QPushButton:hover {{
                background-color: {colors['hover']};
            }}
        """)

    @staticmethod
    def set_light_theme(app: QApplication):
        colors = Theme.LIGHT
        # Gleiche Struktur wie dark_theme, aber mit Light-Farben
        app.setStyleSheet(f"""
            QMainWindow, QDialog {{
                background-color: {colors['bg']};
            }}
            
            QWidget {{
                color: {colors['text']};
                font-family: Segoe UI, Arial;
                font-size: 12px;
            }}
            
            QGroupBox {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: 6px;
                margin-top: 12px;
                padding: 12px;
                font-weight: bold;
            }}
            
            /* ... Rest analog zum Dark Theme ... */
        """) 