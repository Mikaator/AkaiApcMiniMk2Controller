from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, 
                            QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, 
                            QLabel, QFrame, QGroupBox, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPixmap
import sys
from led_controller import (LedController, PadColor, ButtonBehavior, 
                          ButtonType, AnimationType)
import mido
import time
from theme import Theme
import json
import os
from pathlib import Path
from translations import Translations

class LedButton(QPushButton):
    """Repräsentiert einen einzelnen LED-Button im Grid"""
    def __init__(self, note: int, is_rgb: bool = True, parent=None):
        super().__init__(parent)
        self.note = note
        self.is_rgb = is_rgb
        self.press_behavior_enabled = False
        self.button_mode = "Toggle"
        self.pressed_animation = "Statisch"
        self.unpressed_animation = "Statisch"
        self.pressed_color = "RED"     # Neue Attribute für individuelle Farben
        self.unpressed_color = "OFF"
        self.setFixedSize(50, 50)
        self.setColor(PadColor.OFF if is_rgb else None)
        
    def setColor(self, color: PadColor = None):
        """Aktualisiert die Farbe des Buttons"""
        if self.is_rgb and color:
            hex_color = PadColor.get_hex_color(color.value)
            border_color = "#666666"
        else:
            # Einfarbige Buttons (rot oder grün)
            if 0x64 <= self.note <= 0x6B:  # Track Buttons
                hex_color = "#333333"  # Dunkelgrau für aus
                border_color = "#FF0000"  # Roter Rand
            elif 0x70 <= self.note <= 0x77:  # Scene Launch Buttons
                hex_color = "#333333"  # Dunkelgrau für aus
                border_color = "#00FF00"  # Grüner Rand
            else:
                hex_color = "#333333"  # Dunkelgrau für aus
                border_color = "#666666"
                
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {hex_color};
                border: 2px solid {border_color};
                border-radius: 5px;
            }}
            QPushButton:pressed {{
                background-color: #666666;
            }}
        """)

    def set_button_color(self, note: int, is_on: bool):
        """Setzt die Farbe eines nicht-RGB-Buttons"""
        if not self.is_rgb:
            if 0x64 <= self.note <= 0x6B:  # Track Buttons
                hex_color = "#FF0000" if is_on else "#333333"  # Rot wenn an, dunkelgrau wenn aus
                border_color = "#FF0000"
            elif 0x70 <= self.note <= 0x77:  # Scene Launch Buttons
                hex_color = "#00FF00" if is_on else "#333333"  # Grün wenn an, dunkelgrau wenn aus
                border_color = "#00FF00"
                
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {hex_color};
                    border: 2px solid {border_color};
                    border-radius: 5px;
                }}
                QPushButton:pressed {{
                    background-color: #666666;
                }}
            """)

class Dashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("APC mini mk2 Controller")
        self.setMinimumSize(800, 600)
        
        # Controller wird erst später initialisiert
        self.controller = None
        
        # Spracheinstellung vor setup_ui initialisieren
        self.current_language = 'de'  # Standard: Deutsch
        
        # MIDI-Geräte finden
        try:
            self.input_devices = mido.get_input_names()
            self.output_devices = mido.get_output_names()
            print("Verfügbare MIDI-Eingänge:", self.input_devices)
            print("Verfügbare MIDI-Ausgänge:", self.output_devices)
        except Exception as e:
            print(f"Fehler beim Suchen der MIDI-Geräte: {e}")
            self.input_devices = []
            self.output_devices = []
        
        # Logo und Support-Text in Titelleiste
        title_bar = QWidget()
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 10, 10, 10)
        
        # Logo und Titel zusammen
        logo_title_layout = QHBoxLayout()
        logo_title_layout.setSpacing(15)  # Mehr Abstand zwischen Logo und Text
        
        # Logo - noch größer
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
        logo_pixmap = QPixmap(logo_path)
        # Größeres Logo (60x60 statt 40x40)
        logo_pixmap = logo_pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio)
        logo_label.setPixmap(logo_pixmap)
        
        # Titel direkt nach dem Logo
        title_label = QLabel("APC mini mk2 Controller by Mikaator")
        title_label.setStyleSheet("font-size: 14px;")  # Größere Schrift
        
        logo_title_layout.addWidget(logo_label)
        logo_title_layout.addWidget(title_label)
        logo_title_layout.addStretch()
        
        # Support-Text ganz rechts
        support_label = QLabel("Support: michatfragen@gmail.com")
        
        title_layout.addLayout(logo_title_layout)
        title_layout.addStretch()
        title_layout.addWidget(support_label)
        
        # Sprachauswahl zur Titelleiste hinzufügen
        language_combo = QComboBox()
        language_combo.addItems(['Deutsch', 'English'])
        language_combo.currentTextChanged.connect(self.change_language)
        title_layout.addWidget(language_combo)
        
        self.setMenuWidget(title_bar)
        
        # Theme-Schalter hinzufügen
        self.dark_mode = True
        self.settings_file = Path.home() / ".apc_settings.json"
        self.last_config_file = None
        
        # Lade die letzten Einstellungen
        self.load_settings()
        
        # UI aufbauen
        self.setup_ui()
        self.setup_theme_switch()
        
        # Lade die letzte Konfiguration, falls vorhanden
        if self.last_config_file and os.path.exists(self.last_config_file):
            self.load_configuration(self.last_config_file)
        
        # Versuche Controller zu initialisieren, wenn Geräte verfügbar sind
        if self.input_devices:
            self.try_initialize_controller(self.input_devices[0])
            
        self.toggle_states = {}  # Speichert den Toggle-Zustand der Buttons
        
    def try_initialize_controller(self, device_name: str) -> bool:
        """Versucht einen Controller für das gewählte Gerät zu initialisieren"""
        try:
            if self.controller:
                self.controller.cleanup()  # Alte Verbindung schließen
            
            self.controller = LedController(device_name)
            self.controller.add_button_callback(self.handle_midi_input)
            print(f"Controller erfolgreich initialisiert für: {device_name}")
            return True
        except Exception as e:
            print(f"Fehler beim Initialisieren des Controllers für {device_name}: {e}")
            self.controller = None
            return False
            
    def on_device_change(self, device_name: str):
        """Wird aufgerufen, wenn ein anderes MIDI-Gerät ausgewählt wird"""
        if device_name:
            self.try_initialize_controller(device_name)
            
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        
        # Linke Seite: Grid mit zusätzlichen Buttons
        grid_frame = QFrame()
        grid_frame.setFrameStyle(QFrame.Shape.Box)
        grid_layout = QGridLayout(grid_frame)
        
        # Haupt-Grid (8x8)
        self.buttons = {}
        for row in range(8):
            for col in range(8):
                note = (7-row) * 8 + col
                button = LedButton(note, is_rgb=True)
                button.clicked.connect(lambda checked, n=note: self.on_button_click(n))
                self.buttons[note] = button
                grid_layout.addWidget(button, row, col)
        
        # Scene Launch Buttons (rechts)
        for i in range(8):
            note = 0x70 + i  # Scene Launch Button Notes: 0x70-0x77
            button = LedButton(note, is_rgb=False)
            button.clicked.connect(lambda checked, n=note: self.on_button_click(n))
            self.buttons[note] = button
            grid_layout.addWidget(button, i, 8)  # Spalte 8 (nach dem 8x8 Grid)
        
        # Track Buttons (unten)
        for i in range(8):
            note = 0x64 + i  # Track Button Notes: 0x64-0x6B
            button = LedButton(note, is_rgb=False)
            button.clicked.connect(lambda checked, n=note: self.on_button_click(n))
            self.buttons[note] = button
            grid_layout.addWidget(button, 8, i)  # Zeile 8 (nach dem 8x8 Grid)
        
        layout.addWidget(grid_frame)
        
        # Rechte Seite: Kontrollen
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.Shape.Box)
        control_layout = QVBoxLayout(control_frame)
        
        # MIDI-Geräteauswahl
        device_group = QGroupBox(Translations.get_string('midi_devices', self.current_language))
        device_group.setObjectName("device_group")
        device_group_layout = QVBoxLayout()
        
        # Eingangsgerät
        input_layout = QHBoxLayout()
        input_label = QLabel(Translations.get_string('midi_input', self.current_language))
        input_label.setObjectName("midi_input")
        self.input_combo = QComboBox()
        self.input_combo.addItem("Kein Gerät")
        if self.input_devices:
            self.input_combo.addItems(self.input_devices)
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_combo)
        device_group_layout.addLayout(input_layout)
        
        # Ausgangsgerät
        output_layout = QHBoxLayout()
        output_label = QLabel(Translations.get_string('midi_output', self.current_language))
        output_label.setObjectName("midi_output")
        self.output_combo = QComboBox()
        self.output_combo.addItem("Kein Gerät")
        if self.output_devices:
            self.output_combo.addItems(self.output_devices)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_combo)
        device_group_layout.addLayout(output_layout)
        
        # Loopback-Gerät
        loopback_layout = QHBoxLayout()
        loopback_label = QLabel(Translations.get_string('midi_loopback', self.current_language))
        loopback_label.setObjectName("midi_loopback")
        self.loopback_combo = QComboBox()
        self.loopback_combo.addItem("Kein Loopback")
        if self.output_devices:
            self.loopback_combo.addItems(self.output_devices)
        loopback_layout.addWidget(loopback_label)
        loopback_layout.addWidget(self.loopback_combo)
        device_group_layout.addLayout(loopback_layout)
        
        # Verbinden-Button
        connect_button = QPushButton(Translations.get_string('connect', self.current_language))
        connect_button.setObjectName("connect_button")
        connect_button.clicked.connect(self.connect_devices)
        device_group_layout.addWidget(connect_button)
        
        device_group.setLayout(device_group_layout)
        control_layout.addWidget(device_group)
        
        # Farbauswahl und LED-Einstellungen
        color_group = QGroupBox("LED-Einstellungen")
        color_group.setObjectName("led_settings_group")
        color_layout = QVBoxLayout()
        
        # Farbe
        color_row = QHBoxLayout()
        color_label = QLabel("Farbe:")
        self.color_combo = QComboBox()
        self.color_combo.addItems([color.name for color in PadColor])
        color_row.addWidget(color_label)
        color_row.addWidget(self.color_combo)
        color_layout.addLayout(color_row)
        
        # Helligkeit
        brightness_layout = QHBoxLayout()
        brightness_label = QLabel(Translations.get_string('brightness', self.current_language))
        brightness_label.setObjectName("brightness_label")
        self.brightness_combo = QComboBox()
        brightness_options = [
            "10% (Kanal 0)", "25% (Kanal 1)", "50% (Kanal 2)", 
            "65% (Kanal 3)", "75% (Kanal 4)", "90% (Kanal 5)", 
            "100% (Kanal 6)"
        ]
        self.brightness_combo.addItems(brightness_options)
        self.brightness_combo.setCurrentIndex(6)  # Standard: 100%
        brightness_layout.addWidget(brightness_label)
        brightness_layout.addWidget(self.brightness_combo)
        color_layout.addLayout(brightness_layout)

        # Animation
        animation_layout = QHBoxLayout()
        animation_label = QLabel(Translations.get_string('animation', self.current_language))
        animation_label.setObjectName("animation_label")
        self.animation_combo = QComboBox()
        animation_options = [
            "Statisch", 
            "Pulsieren 1/16 (Kanal 7)", "Pulsieren 1/8 (Kanal 8)", 
            "Pulsieren 1/4 (Kanal 9)", "Pulsieren 1/2 (Kanal 10)",
            "Blinken 1/24 (Kanal 11)", "Blinken 1/16 (Kanal 12)", 
            "Blinken 1/8 (Kanal 13)", "Blinken 1/4 (Kanal 14)", 
            "Blinken 1/2 (Kanal 15)"
        ]
        self.animation_combo.addItems(animation_options)
        animation_layout.addWidget(animation_label)
        animation_layout.addWidget(self.animation_combo)
        color_layout.addLayout(animation_layout)
        
        color_group.setLayout(color_layout)
        control_layout.addWidget(color_group)
        
        # Button Press Verhalten (ohne Helligkeit und Animation)
        press_behavior_group = QGroupBox(Translations.get_string('button_behavior', self.current_language))
        press_behavior_group.setObjectName("press_behavior_group")
        press_behavior_layout = QVBoxLayout()
        
        # Button-Modus
        mode_layout = QHBoxLayout()
        mode_label = QLabel(Translations.get_string('mode', self.current_language))
        mode_label.setObjectName("mode_label")
        self.button_mode_combo = QComboBox()
        self.button_mode_combo.addItems(["Flash", "Toggle"])
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.button_mode_combo)
        press_behavior_layout.addLayout(mode_layout)
        
        # Nicht gedrückt/Aus-Zustand
        unpressed_layout = QHBoxLayout()
        unpressed_label = QLabel(Translations.get_string('unpressed_state', self.current_language))
        unpressed_label.setObjectName("unpressed_label")
        self.unpressed_color_combo = QComboBox()
        self.unpressed_color_combo.addItems([color.name for color in PadColor])
        unpressed_layout.addWidget(unpressed_label)
        unpressed_layout.addWidget(self.unpressed_color_combo)
        
        # Helligkeit für nicht gedrückt
        self.unpressed_brightness_combo = QComboBox()
        self.unpressed_brightness_combo.addItems([
            "10%", "25%", "50%", "65%", "75%", "90%", "100%"
        ])
        self.unpressed_brightness_combo.setCurrentIndex(6)  # Standard: 100%
        unpressed_layout.addWidget(self.unpressed_brightness_combo)
        
        # Animation für nicht gedrückt
        self.unpressed_animation_combo = QComboBox()
        self.unpressed_animation_combo.addItems([
            "Statisch", 
            "Pulsieren 1/16", "Pulsieren 1/8", "Pulsieren 1/4", "Pulsieren 1/2",
            "Blinken 1/24", "Blinken 1/16", "Blinken 1/8", "Blinken 1/4", "Blinken 1/2"
        ])
        unpressed_layout.addWidget(self.unpressed_animation_combo)
        press_behavior_layout.addLayout(unpressed_layout)
        
        # Gedrückt/An-Zustand
        pressed_layout = QHBoxLayout()
        pressed_label = QLabel(Translations.get_string('pressed_state', self.current_language))
        pressed_label.setObjectName("pressed_label")
        self.pressed_color_combo = QComboBox()
        self.pressed_color_combo.addItems([color.name for color in PadColor])
        pressed_layout.addWidget(pressed_label)
        pressed_layout.addWidget(self.pressed_color_combo)
        
        # Helligkeit für gedrückt
        self.pressed_brightness_combo = QComboBox()
        self.pressed_brightness_combo.addItems([
            "10%", "25%", "50%", "65%", "75%", "90%", "100%"
        ])
        self.pressed_brightness_combo.setCurrentIndex(6)  # Standard: 100%
        pressed_layout.addWidget(self.pressed_brightness_combo)
        
        # Animation für gedrückt
        self.pressed_animation_combo = QComboBox()
        self.pressed_animation_combo.addItems([
            "Statisch", 
            "Pulsieren 1/16", "Pulsieren 1/8", "Pulsieren 1/4", "Pulsieren 1/2",
            "Blinken 1/24", "Blinken 1/16", "Blinken 1/8", "Blinken 1/4", "Blinken 1/2"
        ])
        pressed_layout.addWidget(self.pressed_animation_combo)
        press_behavior_layout.addLayout(pressed_layout)
        
        # Button Press Modus aktivieren
        self.enable_press_behavior = QPushButton("Button auswählen")
        self.enable_press_behavior.setCheckable(True)
        self.enable_press_behavior.clicked.connect(self.toggle_press_behavior)
        press_behavior_layout.addWidget(self.enable_press_behavior)
        
        press_behavior_group.setLayout(press_behavior_layout)
        control_layout.addWidget(press_behavior_group)
        
        # Aktions-Buttons
        clear_button = QPushButton("Alle LEDs aus")
        clear_button.clicked.connect(self.on_clear_all)
        control_layout.addWidget(clear_button)
        
        control_layout.addStretch()
        layout.addWidget(control_frame)
        
        # Animations-Gruppe hinzufügen
        animation_group = QGroupBox(Translations.get_string('animations', self.current_language))
        animation_group.setObjectName("animation_group")
        animation_layout = QVBoxLayout()
        
        # Alle LEDs an/aus
        all_leds_layout = QHBoxLayout()
        all_on_button = QPushButton(Translations.get_string('all_leds_on', self.current_language))
        all_on_button.setObjectName("all_leds_on")
        all_on_button.clicked.connect(lambda: self.set_all_leds(True))
        all_off_button = QPushButton(Translations.get_string('all_leds_off', self.current_language))
        all_off_button.setObjectName("all_leds_off")
        all_off_button.clicked.connect(lambda: self.set_all_leds(False))
        all_leds_layout.addWidget(all_on_button)
        all_leds_layout.addWidget(all_off_button)
        animation_layout.addLayout(all_leds_layout)
        
        # Animations-Auswahl
        animation_combo = QComboBox()
        animation_combo.addItems([anim.value for anim in AnimationType])
        animation_layout.addWidget(animation_combo)
        
        # Start/Stop Buttons
        animation_buttons_layout = QHBoxLayout()
        start_button = QPushButton(Translations.get_string('start_animation', self.current_language))
        start_button.setObjectName("start_animation")
        start_button.clicked.connect(
            lambda: self.start_animation(AnimationType(animation_combo.currentText()))
        )
        stop_button = QPushButton(Translations.get_string('stop_animation', self.current_language))
        stop_button.setObjectName("stop_animation")
        stop_button.clicked.connect(self.stop_animation)
        animation_buttons_layout.addWidget(start_button)
        animation_buttons_layout.addWidget(stop_button)
        animation_layout.addLayout(animation_buttons_layout)
        
        animation_group.setLayout(animation_layout)
        control_layout.addWidget(animation_group)
        
        # Speichern/Laden Buttons zur Control-Seite hinzufügen
        save_load_group = QGroupBox(Translations.get_string('configuration', self.current_language))
        save_load_group.setObjectName("config_group")
        save_load_layout = QVBoxLayout()
        
        save_button = QPushButton(Translations.get_string('save_config', self.current_language))
        save_button.setObjectName("save_config")
        save_button.clicked.connect(self.save_configuration)
        save_load_layout.addWidget(save_button)
        
        load_button = QPushButton(Translations.get_string('load_config', self.current_language))
        load_button.setObjectName("load_config")
        load_button.clicked.connect(self.load_configuration)
        save_load_layout.addWidget(load_button)
        
        save_load_group.setLayout(save_load_layout)
        control_layout.addWidget(save_load_group)
        
        # Layout-Abstände anpassen
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)
        
        grid_layout.setSpacing(2)  # Geringerer Abstand zwischen Grid-Buttons
        control_layout.setSpacing(4)
        
        # Minimale Breite für die Control-Seite
        control_frame.setMinimumWidth(250)
        
        # Maximale Breite für ComboBoxen
        for combo in [self.input_combo, self.output_combo, self.loopback_combo,
                     self.color_combo, self.brightness_combo, self.animation_combo]:
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumContentsLength(15)  # Minimale Anzahl sichtbarer Zeichen

    def on_button_click(self, note: int):
        """Wird aufgerufen, wenn ein Button im Grid geklickt wird"""
        if not self.controller:
            print("Kein MIDI-Controller verbunden")
            return
        
        button = self.buttons[note]
        
        # Initialen Zustand setzen
        if self.enable_press_behavior.isChecked():
            button.press_behavior_enabled = True
            button.button_mode = self.button_mode_combo.currentText()
            button.pressed_animation = self.pressed_animation_combo.currentText()
            button.unpressed_animation = self.unpressed_animation_combo.currentText()
            button.pressed_color = self.pressed_color_combo.currentText()
            button.unpressed_color = self.unpressed_color_combo.currentText()
            button.pressed_brightness = self.pressed_brightness_combo.currentIndex()
            button.unpressed_brightness = self.unpressed_brightness_combo.currentIndex()
            self.enable_press_behavior.setChecked(False)
            print(f"Button {note} verwendet jetzt Button Press Verhalten ({button.button_mode})")
            
            # Initialen Zustand setzen (immer den "nicht gedrückt" Zustand)
            if button.button_mode == "Toggle":
                # Für RGB Buttons
                if not (0x64 <= note <= 0x6B or 0x70 <= note <= 0x77):
                    color = PadColor[button.unpressed_color]
                    if button.unpressed_animation == "Statisch":
                        channel = button.unpressed_brightness
                    else:
                        channel = self.get_animation_channel(button.unpressed_animation)
                    self.controller.set_pad_color(note, color, channel=channel)
                    self.buttons[note].setColor(color)
                # Für Track/Scene Buttons
                else:
                    velocity = 0  # Initial ausgeschaltet
                    self.controller.set_button_color(ButtonType(note), velocity)
                self.toggle_states[note] = False  # Initial nicht getoggelt
                return
            else:  # Flash-Modus
                # Für RGB Buttons
                if not (0x64 <= note <= 0x6B or 0x70 <= note <= 0x77):
                    color = PadColor[button.unpressed_color]
                    if button.unpressed_animation == "Statisch":
                        channel = button.unpressed_brightness
                    else:
                        channel = self.get_animation_channel(button.unpressed_animation)
                    self.controller.set_pad_color(note, color, channel=channel)
                    self.buttons[note].setColor(color)
                # Für Track/Scene Buttons
                else:
                    velocity = 0  # Initial ausgeschaltet
                    self.controller.set_button_color(ButtonType(note), velocity)
                return

        # Track/Scene Buttons
        if 0x64 <= note <= 0x6B or 0x70 <= note <= 0x77:
            if button.press_behavior_enabled:
                if button.button_mode == "Toggle":
                    self.toggle_states[note] = not self.toggle_states.get(note, False)
                    if self.toggle_states[note]:
                        is_blinking = "Blinken" in button.pressed_animation  # Verwende Button-spezifische Animation
                        velocity = 2 if is_blinking else 1
                    else:
                        velocity = 0
                    self.controller.set_button_color(ButtonType(note), velocity)
                    button.set_button_color(note, velocity > 0)  # Update UI
                else:  # Flash-Modus
                    is_blinking = "Blinken" in button.pressed_animation  # Verwende Button-spezifische Animation
                    velocity = 2 if is_blinking else 1
                    self.controller.set_button_color(ButtonType(note), velocity)
                    button.set_button_color(note, True)  # Update UI
            else:
                # Normales Verhalten
                if self.color_combo.currentText() == "OFF":
                    velocity = 0
                else:
                    is_blinking = "Blinken" in self.animation_combo.currentText()
                    velocity = 2 if is_blinking else 1
                self.controller.set_button_color(ButtonType(note), velocity)
                button.set_button_color(note, velocity > 0)  # Update UI
        # RGB Buttons
        else:
            if button.press_behavior_enabled:
                if button.button_mode == "Toggle":
                    # Toggle-Zustand umschalten
                    self.toggle_states[note] = not self.toggle_states.get(note, False)
                    if self.toggle_states[note]:
                        color = PadColor[button.pressed_color]    # Verwende Button-spezifische Farben
                        channel = self.get_animation_channel(button.pressed_animation)
                    else:
                        color = PadColor[button.unpressed_color]
                        channel = self.get_animation_channel(button.unpressed_animation)
                    self.controller.set_pad_color(note, color, channel=channel)
                    self.buttons[note].setColor(color)
                else:  # Flash-Modus
                    color = PadColor[button.pressed_color]    # Verwende Button-spezifische Farben
                    channel = self.get_animation_channel(button.pressed_animation)
                    self.controller.set_pad_color(note, color, channel=channel)
                    self.buttons[note].setColor(color)
            else:
                # Normales Verhalten
                color = PadColor[self.color_combo.currentText()]
                if self.animation_combo.currentText().startswith("Statisch"):
                    channel = self.brightness_combo.currentIndex()
                else:
                    channel = 7 + self.animation_combo.currentIndex() - 1
                self.controller.set_pad_color(note, color, channel=channel)
                self.buttons[note].setColor(color)
                # Speichere die individuellen Button-Einstellungen
                button.setProperty('current_color', self.color_combo.currentText())
                button.setProperty('current_animation', self.animation_combo.currentText())
                button.setProperty('is_on', color != PadColor.OFF)

    def on_clear_all(self):
        """Schaltet alle LEDs aus"""
        if not self.controller:
            print("Kein MIDI-Controller verbunden")
            return
            
        self.controller.clear_all()
        for button in self.buttons.values():
            button.setColor(PadColor.OFF)
            
    def handle_midi_input(self, msg):
        """Verarbeitet eingehende MIDI-Nachrichten"""
        if msg.type in ['note_on', 'note_off']:
            if msg.note in self.buttons:
                button = self.buttons[msg.note]
                
                # Track/Scene Buttons
                if 0x64 <= msg.note <= 0x6B or 0x70 <= msg.note <= 0x77:
                    if button.press_behavior_enabled:
                        if button.button_mode == "Toggle":
                            if msg.type == 'note_on':
                                self.toggle_states[msg.note] = not self.toggle_states.get(msg.note, False)
                                if self.toggle_states[msg.note]:
                                    is_blinking = "Blinken" in button.pressed_animation
                                    velocity = 2 if is_blinking else 1
                                else:
                                    velocity = 0
                                self.controller.set_button_color(ButtonType(msg.note), velocity)
                        else:  # Flash-Modus
                            if msg.type == 'note_on':
                                is_blinking = "Blinken" in button.pressed_animation
                                velocity = 2 if is_blinking else 1
                            else:
                                velocity = 0
                            self.controller.set_button_color(ButtonType(msg.note), velocity)
                # RGB Buttons
                else:
                    if button.press_behavior_enabled:
                        if button.button_mode == "Toggle":
                            if msg.type == 'note_on':
                                self.toggle_states[msg.note] = not self.toggle_states.get(msg.note, False)
                                if self.toggle_states[msg.note]:
                                    color = PadColor[button.pressed_color]    # Verwende Button-spezifische Farben
                                    channel = self.get_animation_channel(button.pressed_animation)
                                else:
                                    color = PadColor[button.unpressed_color]    # Verwende Button-spezifische Farben
                                    channel = self.get_animation_channel(button.unpressed_animation)
                                self.controller.set_pad_color(msg.note, color, channel=channel)
                                self.buttons[msg.note].setColor(color)
                        else:  # Flash-Modus
                            if msg.type == 'note_on':
                                color = PadColor[button.pressed_color]    # Verwende Button-spezifische Farben
                                channel = self.get_animation_channel(button.pressed_animation)
                            else:
                                color = PadColor[button.unpressed_color]    # Verwende Button-spezifische Farben
                                channel = self.get_animation_channel(button.unpressed_animation)
                            self.controller.set_pad_color(msg.note, color, channel=channel)
                            self.buttons[msg.note].setColor(color)

    def connect_devices(self):
        """Verbindet die ausgewählten MIDI-Geräte"""
        input_device = self.input_combo.currentText()
        output_device = self.output_combo.currentText()
        loopback_device = self.loopback_combo.currentText()
        
        if input_device == "Kein Gerät" or output_device == "Kein Gerät":
            print("Bitte wähle Ein- und Ausgangsgerät aus")
            return
            
        # Wenn "Kein Loopback" gewählt wurde, None verwenden
        loopback_device = None if loopback_device == "Kein Loopback" else loopback_device
        
        try:
            if self.controller:
                self.controller.cleanup()
            
            self.controller = LedController(input_device, output_device, loopback_device)
            self.controller.add_button_callback(self.handle_midi_input)
            print(f"Controller erfolgreich initialisiert mit IN={input_device}, OUT={output_device}, LOOP={loopback_device}")
        except Exception as e:
            print(f"Fehler beim Verbinden der Geräte: {e}")
            self.controller = None

    def set_all_leds(self, on: bool):
        """Schaltet alle LEDs ein oder aus"""
        if not self.controller:
            print("Kein MIDI-Controller verbunden")
            return
        
        color = PadColor.WHITE if on else PadColor.OFF
        # Verwende aktuelle Helligkeits-/Animations-Einstellungen
        if self.animation_combo.currentText().startswith("Statisch"):
            channel = self.brightness_combo.currentIndex()
        else:
            channel = 7 + self.animation_combo.currentIndex() - 1
        
        for note in range(64):
            self.controller.set_pad_color(note, color, channel=channel)
            self.buttons[note].setColor(color)

    def start_animation(self, animation_type: AnimationType):
        """Startet die ausgewählte Animation"""
        if not self.controller:
            print("Kein MIDI-Controller verbunden")
            return
            
        self.controller.start_animation(animation_type)

    def stop_animation(self):
        """Stoppt die laufende Animation"""
        if not self.controller:
            print("Kein MIDI-Controller verbunden")
            return
            
        self.controller.stop_animation()

    def update_midi_settings(self):
        """Aktualisiert die MIDI-Einstellungen für alle Buttons im Grid."""
        if not self.controller:
            print("Kein MIDI-Controller verbunden. Bitte verbinden Sie die Geräte.")
            return
        
        for note, button in self.buttons.items():
            color = PadColor[self.color_combo.currentText()]  # Verwenden Sie die ausgewählte Farbe
            channel = int(button.channel_combo.currentText()) - 1  # 0-indexiert
            velocity = int(button.velocity_combo.currentText())
            
            # Debug-Ausgabe
            print(f"Button {note} - Kanal: {channel}, Velocity: {velocity}")
            
            # Setzen Sie die Farbe mit dem ausgewählten Kanal und der Velocity
            self.controller.set_pad_color(note, color, channel, velocity)
            button.setColor(color)  # Aktualisieren Sie die Button-Farbe

    def toggle_press_behavior(self):
        """Aktiviert den Auswahlmodus für Button Press Verhalten"""
        if self.enable_press_behavior.isChecked():
            print("Wähle einen Button aus, um Button Press Verhalten zu aktivieren")
        else:
            print("Button-Auswahl abgebrochen")

    def get_animation_channel(self, animation_text: str) -> int:
        """Ermittelt den MIDI-Kanal für die gewählte Animation"""
        if animation_text == "Statisch":
            return 6  # 100% Helligkeit
        
        animations = {
            "Pulsieren 1/16": 7, "Pulsieren 1/8": 8, 
            "Pulsieren 1/4": 9, "Pulsieren 1/2": 10,
            "Blinken 1/24": 11, "Blinken 1/16": 12,
            "Blinken 1/8": 13, "Blinken 1/4": 14,
            "Blinken 1/2": 15
        }
        return animations.get(animation_text, 6)

    def setup_theme_switch(self):
        """Fügt einen Theme-Schalter hinzu"""
        theme_button = QPushButton("🌙" if self.dark_mode else "☀️")
        theme_button.setFixedSize(30, 30)
        theme_button.clicked.connect(self.toggle_theme)
        theme_button.setStyleSheet("""
            QPushButton {
                border-radius: 15px;
                font-size: 16px;
            }
        """)
        
        # Button in die Titelleiste einfügen
        toolbar = self.addToolBar("Theme")
        toolbar.addWidget(theme_button)
        
    def toggle_theme(self):
        """Wechselt zwischen Light und Dark Theme"""
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            Theme.set_dark_theme(QApplication.instance())
            self.sender().setText("🌙")
        else:
            Theme.set_light_theme(QApplication.instance())
            self.sender().setText("☀️")

    def update_single_track_button(self, index: int):
        """Aktualisiert einen einzelnen Track Button"""
        if not self.controller:
            return
        
        note = 0x64 + index
        button = self.buttons[note]
        is_on = button.track_button.isChecked()
        is_blinking = button.track_blink.currentText() == "Blinken"
        
        velocity = 2 if (is_on and is_blinking) else (1 if is_on else 0)
        self.controller.set_button_color(ButtonType(note), velocity)
        button.setColor()

    def update_single_scene_button(self, index: int):
        """Aktualisiert einen einzelnen Scene Button"""
        if not self.controller:
            return
        
        note = 0x70 + index
        button = self.buttons[note]
        is_on = button.scene_button.isChecked()
        is_blinking = button.scene_blink.currentText() == "Blinken"
        
        velocity = 2 if (is_on and is_blinking) else (1 if is_on else 0)
        self.controller.set_button_color(ButtonType(note), velocity)
        button.setColor()

    def save_configuration(self, filename=None):
        """Speichert die aktuelle Konfiguration"""
        if not filename:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Konfiguration speichern",
                str(Path.home()),
                "JSON Dateien (*.json)"
            )
            if not filename:
                return
        
        config = {
            'midi_devices': {
                'input': self.input_combo.currentText(),
                'output': self.output_combo.currentText(),
                'loopback': self.loopback_combo.currentText()
            },
            'global_settings': {
                'color': self.color_combo.currentText(),
                'brightness': self.brightness_combo.currentText(),
                'animation': self.animation_combo.currentText(),
                'button_mode': self.button_mode_combo.currentText(),
                'pressed_color': self.pressed_color_combo.currentText(),
                'pressed_animation': self.pressed_animation_combo.currentText(),
                'pressed_brightness': self.pressed_brightness_combo.currentIndex(),
                'unpressed_color': self.unpressed_color_combo.currentText(),
                'unpressed_animation': self.unpressed_animation_combo.currentText(),
                'unpressed_brightness': self.unpressed_brightness_combo.currentIndex(),
            },
            'button_states': {
                str(note): {
                    'press_behavior_enabled': button.press_behavior_enabled,
                    'button_mode': button.button_mode,
                    'pressed_animation': button.pressed_animation,
                    'unpressed_animation': button.unpressed_animation,
                    'pressed_color': button.pressed_color,
                    'unpressed_color': button.unpressed_color,
                    'pressed_brightness': getattr(button, 'pressed_brightness', 6),
                    'unpressed_brightness': getattr(button, 'unpressed_brightness', 6),
                    'toggle_state': self.toggle_states.get(note, False),
                    'current_color': button.property('current_color') or self.color_combo.currentText(),
                    'current_animation': button.property('current_animation') or self.animation_combo.currentText(),
                    'is_on': button.property('is_on') if not (0x64 <= note <= 0x6B or 0x70 <= note <= 0x77) else False
                } for note, button in self.buttons.items()
            }
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(config, f, indent=4)
            print(f"Konfiguration gespeichert in: {filename}")
            
            self.last_config_file = filename
            self.save_settings()
        except Exception as e:
            print(f"Fehler beim Speichern der Konfiguration: {e}")

    def load_configuration(self, filename=None):
        """Lädt eine Konfiguration"""
        if not filename:
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Konfiguration laden",
                str(Path.home()),
                "JSON Dateien (*.json)"
            )
            if not filename:
                return
        
        try:
            with open(filename, 'r') as f:
                config = json.load(f)
            
            # MIDI-Geräte setzen, falls verfügbar
            midi_devices = config.get('midi_devices', {})
            input_device = midi_devices.get('input')
            output_device = midi_devices.get('output')
            loopback_device = midi_devices.get('loopback')
            
            if input_device in self.input_devices:
                self.input_combo.setCurrentText(input_device)
            if output_device in self.output_devices:
                self.output_combo.setCurrentText(output_device)
            if loopback_device in self.output_devices or loopback_device == "Kein Loopback":
                self.loopback_combo.setCurrentText(loopback_device)
            
            # Verbinde die MIDI-Geräte
            self.connect_devices()
            
            # Setze die globalen UI-Elemente
            global_settings = config['global_settings']
            self.color_combo.setCurrentText(global_settings['color'])
            self.brightness_combo.setCurrentText(global_settings['brightness'])
            self.animation_combo.setCurrentText(global_settings['animation'])
            self.button_mode_combo.setCurrentText(global_settings['button_mode'])
            self.pressed_color_combo.setCurrentText(global_settings['pressed_color'])
            self.pressed_animation_combo.setCurrentText(global_settings['pressed_animation'])
            self.pressed_brightness_combo.setCurrentIndex(global_settings.get('pressed_brightness', 6))
            self.unpressed_color_combo.setCurrentText(global_settings['unpressed_color'])
            self.unpressed_animation_combo.setCurrentText(global_settings['unpressed_animation'])
            self.unpressed_brightness_combo.setCurrentIndex(global_settings.get('unpressed_brightness', 6))
            
            # Zuerst alle Buttons zurücksetzen
            self.toggle_states.clear()
            for button in self.buttons.values():
                button.press_behavior_enabled = False
                button.setProperty('current_color', PadColor.OFF.name)
                if 0x64 <= button.note <= 0x6B or 0x70 <= button.note <= 0x77:
                    self.controller.set_button_color(ButtonType(button.note), 0)
                else:
                    self.controller.set_pad_color(button.note, PadColor.OFF)
                    button.setColor(PadColor.OFF)
            
            # Dann die gespeicherten Zustände laden
            for note_str, state in config['button_states'].items():
                note = int(note_str)
                if note in self.buttons:
                    button = self.buttons[note]
                    button.press_behavior_enabled = state['press_behavior_enabled']
                    button.button_mode = state.get('button_mode', 'Toggle')
                    button.pressed_animation = state.get('pressed_animation', 'Statisch')
                    button.unpressed_animation = state.get('unpressed_animation', 'Statisch')
                    button.pressed_color = state.get('pressed_color', 'RED')
                    button.unpressed_color = state.get('unpressed_color', 'OFF')
                    self.toggle_states[note] = state['toggle_state']
                    
                    if button.press_behavior_enabled:
                        if 0x64 <= note <= 0x6B or 0x70 <= note <= 0x77:  # Track/Scene Buttons
                            if self.toggle_states[note]:  # Wenn getoggelt
                                is_blinking = "Blinken" in button.pressed_animation
                                velocity = 2 if is_blinking else 1
                                self.controller.set_button_color(ButtonType(note), velocity)
                            else:
                                self.controller.set_button_color(ButtonType(note), 0)
                        else:  # RGB Buttons
                            if button.button_mode == "Toggle":
                                if self.toggle_states[note]:
                                    color = PadColor[button.pressed_color]
                                    channel = self.get_animation_channel(button.pressed_animation)
                                else:
                                    color = PadColor[button.unpressed_color]
                                    channel = self.get_animation_channel(button.unpressed_animation)
                            else:  # Flash-Modus
                                color = PadColor[button.unpressed_color]
                                channel = self.get_animation_channel(button.unpressed_animation)
                            self.controller.set_pad_color(note, color, channel=channel)
                            button.setColor(color)
                    else:  # Nicht-Press-Behavior Buttons
                        if 0x64 <= note <= 0x6B or 0x70 <= note <= 0x77:
                            if state.get('is_on', False):
                                is_blinking = "Blinken" in state['current_animation']
                                velocity = 2 if is_blinking else 1
                                self.controller.set_button_color(ButtonType(note), velocity)
                        else:
                            if state.get('is_on', False):
                                color = PadColor[state['current_color']]
                                if state['current_animation'].startswith("Statisch"):
                                    channel = self.brightness_combo.currentIndex()
                                else:
                                    channel = 7 + self.animation_combo.currentIndex() - 1
                                self.controller.set_pad_color(note, color, channel=channel)
                                button.setColor(color)
                                button.setProperty('current_color', state['current_color'])
                                button.setProperty('current_animation', state['current_animation'])
                                button.setProperty('is_on', True)
            
            print(f"Konfiguration geladen aus: {filename}")
            self.last_config_file = filename
            self.save_settings()
        except Exception as e:
            print(f"Fehler beim Laden der Konfiguration: {e}")

    def save_settings(self):
        """Speichert die Anwendungseinstellungen"""
        settings = {
            'last_config_file': self.last_config_file
        }
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Fehler beim Speichern der Einstellungen: {e}")

    def load_settings(self):
        """Lädt die Anwendungseinstellungen"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                self.last_config_file = settings.get('last_config_file')
        except Exception as e:
            print(f"Fehler beim Laden der Einstellungen: {e}")

    def change_language(self, language: str):
        """Ändert die Sprache der UI"""
        self.current_language = 'en' if language == 'English' else 'de'
        self.update_ui_texts()

    def update_ui_texts(self):
        """Aktualisiert alle UI-Texte in der gewählten Sprache"""
        # Fenster-Titel
        self.setWindowTitle(Translations.get_string('window_title', self.current_language))
        
        # MIDI-Geräte Gruppe
        self.findChild(QGroupBox, "device_group").setTitle(
            Translations.get_string('midi_devices', self.current_language))
        self.findChild(QLabel, "midi_input").setText(
            Translations.get_string('midi_input', self.current_language))
        self.findChild(QLabel, "midi_output").setText(
            Translations.get_string('midi_output', self.current_language))
        self.findChild(QLabel, "midi_loopback").setText(
            Translations.get_string('midi_loopback', self.current_language))
        self.findChild(QPushButton, "connect_button").setText(
            Translations.get_string('connect', self.current_language))
            
        # Button Press Verhalten
        self.findChild(QGroupBox, "press_behavior_group").setTitle(
            Translations.get_string('button_behavior', self.current_language))
            
        # LED Einstellungen innerhalb der Button Press Gruppe
        self.findChild(QLabel, "brightness_label").setText(
            Translations.get_string('brightness', self.current_language))
        self.findChild(QLabel, "animation_label").setText(
            Translations.get_string('animation', self.current_language))
            
        # Mode, Pressed, Unpressed
        self.findChild(QLabel, "mode_label").setText(
            Translations.get_string('mode', self.current_language))
        self.findChild(QLabel, "unpressed_label").setText(
            Translations.get_string('unpressed_state', self.current_language))
        self.findChild(QLabel, "pressed_label").setText(
            Translations.get_string('pressed_state', self.current_language))
        self.enable_press_behavior.setText(
            Translations.get_string('select_button', self.current_language))
            
        # Animationen
        self.findChild(QGroupBox, "animation_group").setTitle(
            Translations.get_string('animations', self.current_language))
        self.findChild(QPushButton, "all_leds_on").setText(
            Translations.get_string('all_leds_on', self.current_language))
        self.findChild(QPushButton, "all_leds_off").setText(
            Translations.get_string('all_leds_off', self.current_language))
        self.findChild(QPushButton, "start_animation").setText(
            Translations.get_string('start_animation', self.current_language))
        self.findChild(QPushButton, "stop_animation").setText(
            Translations.get_string('stop_animation', self.current_language))
            
        # Konfiguration
        self.findChild(QGroupBox, "config_group").setTitle(
            Translations.get_string('configuration', self.current_language))
        self.findChild(QPushButton, "save_config").setText(
            Translations.get_string('save_config', self.current_language))
        self.findChild(QPushButton, "load_config").setText(
            Translations.get_string('load_config', self.current_language))

def main():
    app = QApplication(sys.argv)
    
    # Dark Mode als Standard
    Theme.set_dark_theme(app)
    
    window = Dashboard()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 