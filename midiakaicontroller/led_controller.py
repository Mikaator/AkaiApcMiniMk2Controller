from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Tuple, Dict
import mido
import threading
import time
import math
import random

class PadColor(Enum):
    """Farben für die Haupt-Pads mit den offiziellen RGB-Werten"""
    OFF = 0         # #000000
    DIM = 1         # #1E1E1E
    GRAY = 2        # #7F7F7F
    WHITE = 3       # #FFFFFF
    LIGHT_RED = 4   # #FF4C4C
    RED = 5         # #FF0000
    DARK_RED = 6    # #590000
    VERY_DARK_RED = 7  # #190000
    LIGHT_ORANGE = 8   # #FFBD6C
    ORANGE = 9        # #FF5400
    DARK_ORANGE = 10  # #591D00
    BROWN = 11        # #271B00
    LIGHT_YELLOW = 12 # #FFFF4C
    YELLOW = 13       # #FFFF00
    DARK_YELLOW = 14  # #595900
    VERY_DARK_YELLOW = 15  # #191900
    LIGHT_LIME = 16   # #88FF4C
    LIME = 17         # #54FF00
    DARK_LIME = 18    # #1D5900
    VERY_DARK_LIME = 19  # #142B00
    LIGHT_GREEN = 20  # #4CFF4C
    GREEN = 21        # #00FF00
    DARK_GREEN = 22   # #005900
    VERY_DARK_GREEN = 23  # #001900
    LIGHT_BLUE = 44   # #4C4CFF
    BLUE = 45         # #0000FF
    DARK_BLUE = 46    # #000059
    VERY_DARK_BLUE = 47  # #000019
    
    @classmethod
    def get_hex_color(cls, color_value: int) -> str:
        """Gibt den Hex-Farbcode für einen Velocity-Wert zurück"""
        color_map = {
            0: "#000000",  # Schwarz/Aus
            1: "#1E1E1E",  # Gedimmt
            2: "#7F7F7F",  # Grau
            3: "#FFFFFF",  # Weiß
            4: "#FF4C4C",  # Helles Rot
            5: "#FF0000",  # Rot
            6: "#590000",  # Dunkles Rot
            7: "#190000",  # Sehr dunkles Rot
            8: "#FFBD6C",  # Helles Orange
            9: "#FF5400",  # Orange
            10: "#591D00", # Dunkles Orange
            11: "#271B00", # Braun
            12: "#FFFF4C", # Helles Gelb
            13: "#FFFF00", # Gelb
            14: "#595900", # Dunkles Gelb
            15: "#191900", # Sehr dunkles Gelb
            16: "#88FF4C", # Helles Limette
            17: "#54FF00", # Limette
            18: "#1D5900", # Dunkles Limette
            19: "#142B00", # Sehr dunkles Limette
            20: "#4CFF4C", # Helles Grün
            21: "#00FF00", # Grün
            22: "#005900", # Dunkles Grün
            23: "#001900", # Sehr dunkles Grün
            44: "#4C4CFF",  # Helles Blau
            45: "#0000FF",  # Blau  
            46: "#000059",  # Dunkles Blau
            47: "#000019",  # Sehr dunkles Blau
        }
        return color_map.get(color_value, "#000000")

class ButtonBehavior(Enum):
    """Verhaltensweisen für LEDs"""
    SOLID = 0   # Dauerhaft an
    BLINK = 1   # Blinken
    PULSE = 2   # Pulsieren

class ButtonType(Enum):
    """Button-Typen und ihre MIDI-Noten"""
    # Track Buttons (Rot)
    TRACK_1 = 0x64
    TRACK_2 = 0x65
    TRACK_3 = 0x66
    TRACK_4 = 0x67
    TRACK_5 = 0x68
    TRACK_6 = 0x69
    TRACK_7 = 0x6A
    TRACK_8 = 0x6B
    
    # Scene Launch Buttons (Grün)
    SCENE_1 = 0x70
    SCENE_2 = 0x71
    SCENE_3 = 0x72
    SCENE_4 = 0x73
    SCENE_5 = 0x74
    SCENE_6 = 0x75
    SCENE_7 = 0x76
    SCENE_8 = 0x77

class AnimationType(Enum):
    """Verschiedene Animations-Typen"""
    RAINBOW = "Regenbogen"
    WAVE = "Welle"
    RAIN = "Regen"
    SNAKE = "Schlange"
    RIPPLE = "Wassertropfen"
    RANDOM = "Zufällig"
    SPIRAL = "Spirale"
    FIREWORK = "Feuerwerk"
    PULSE = "Pulsieren"
    COLOR_WIPE = "Farbwischer"
    ENERGY_FIELD = "Energiefeld"
    BOUNCE = "Prallen"
    SPARKLE = "Funkeln"
    DNA = "DNA-Helix"
    CHASE = "Verfolgung"
    TETRIS = "Tetris"
    LASER = "Laser"
    GALAXY = "Galaxie"
    PIANO = "Piano"
    EQUALIZER = "Equalizer"

@dataclass
class LedState:
    color: PadColor
    behavior: ButtonBehavior = ButtonBehavior.SOLID
    is_on: bool = True

class LedController:
    def __init__(self, input_name: str, output_name: str, loopback_name: str = None):
        try:
            self.input_port = mido.open_input(input_name)
            self.output_port = mido.open_output(output_name)
            
            # Loopback-Port konfigurieren
            self.loopback_port = None
            if loopback_name:
                try:
                    self.loopback_port = mido.open_output(loopback_name)
                    print(f"MIDI-Loopback geöffnet: {loopback_name}")
                except Exception as e:
                    print(f"Fehler beim Öffnen des Loopback-Ports: {e}")
            
            print(f"MIDI-Ports geöffnet: IN={input_name}, OUT={output_name}")
        except Exception as e:
            print(f"Fehler beim Öffnen der MIDI-Ports: {e}")
            self.cleanup()
            raise
            
        self.led_states: Dict[int, LedState] = {}
        self.running = True
        self.button_callbacks = []
        
        self.channel = 9  # Kanal 10 (0-indexiert)
        
        self.input_thread = threading.Thread(target=self._handle_input)
        self.input_thread.daemon = True
        self.input_thread.start()
        
        self.animation_running = False
        self.animation_thread = None

    def set_pad_color(self, note: int, color: PadColor, channel: int = 6):
        """
        Setzt die Farbe und das Verhalten eines Pads
        
        Args:
            note: MIDI-Note (0-63 für das 8x8 Grid)
            color: Gewünschte Farbe aus dem PadColor Enum
            channel: MIDI-Kanal (0-15) für Helligkeit und Animationen:
                    0-6: Helligkeit (10%-100%)
                    7-10: Pulsieren (1/16 bis 1/2)
                    11-15: Blinken (1/24 bis 1/2)
        """
        if not (0 <= channel <= 15):
            raise ValueError("Kanal muss zwischen 0 und 15 liegen")
        
        self.led_states[note] = LedState(color=color)
        self.output_port.send(mido.Message('note_on', 
                                         note=note,
                                         velocity=color.value,
                                         channel=channel))
        
    def set_button_color(self, button: ButtonType, velocity: int = 1):
        """
        Schaltet einen Seiten-Button ein oder aus
        
        Args:
            button: Der zu steuernde Button
            velocity: 0 = aus, 1 = an, 2 = blinken
        """
        self.output_port.send(mido.Message('note_on',
                                         note=button.value,
                                         velocity=velocity,
                                         channel=0))  # Kanal 0 für nicht-RGB Buttons
        
    def set_grid_pattern(self, pattern: List[List[PadColor]]):
        """
        Setzt ein 8x8 Muster auf dem Pad-Grid
        
        Args:
            pattern: 8x8 Liste mit Farben
        """
        for row in range(8):
            for col in range(8):
                note = row * 8 + col
                self.set_pad_color(note, pattern[row][col])
                
    def clear_all(self):
        """Schaltet alle LEDs aus"""
        # Grid löschen
        for note in range(64):
            self.set_pad_color(note, PadColor.OFF)
            
        # Track Buttons löschen
        for button in ButtonType:
            self.set_button_color(button, False)
            
    def cleanup(self):
        """Schließt alle offenen Ports und beendet Threads"""
        self.running = False
        
        if hasattr(self, 'input_port') and self.input_port:
            self.input_port.close()
            self.input_port = None
            
        if hasattr(self, 'output_port') and self.output_port:
            self.output_port.close()
            self.output_port = None
            
        if hasattr(self, 'loopback_port') and self.loopback_port:
            self.loopback_port.close()
            self.loopback_port = None
            
    def add_button_callback(self, callback):
        """Fügt einen Callback für Button-Events hinzu"""
        self.button_callbacks.append(callback)
        
    def _handle_input(self):
        """Verarbeitet eingehende MIDI-Nachrichten"""
        while self.running:
            try:
                for msg in self.input_port:
                    # Weiterleitung an Loopback-Port
                    if self.loopback_port:
                        self.loopback_port.send(msg)
                    
                    # Normale Verarbeitung
                    for callback in self.button_callbacks:
                        callback(msg)
            except Exception as e:
                print(f"Fehler beim Verarbeiten der MIDI-Nachricht: {e}")
                
    def __del__(self):
        self.cleanup() 
        
    def set_all_pads(self, color: PadColor):
        """Setzt alle Pads auf eine Farbe"""
        for note in range(64):
            self.set_pad_color(note, color)
            
    def start_animation(self, animation_type: AnimationType):
        """Startet eine Animation"""
        if self.animation_thread and self.animation_thread.is_alive():
            self.stop_animation()
            
        self.animation_running = True
        self.animation_thread = threading.Thread(
            target=self._run_animation,
            args=(animation_type,)
        )
        self.animation_thread.daemon = True
        self.animation_thread.start()
        
    def stop_animation(self):
        """Stoppt die laufende Animation"""
        self.animation_running = False
        if self.animation_thread:
            self.animation_thread.join(timeout=1.0)
            
    def _run_animation(self, animation_type: AnimationType):
        """Führt die ausgewählte Animation aus"""
        animations = {
            AnimationType.RAINBOW: self._rainbow_animation,
            AnimationType.WAVE: self._wave_animation,
            AnimationType.RAIN: self._rain_animation,
            AnimationType.SNAKE: self._snake_animation,
            AnimationType.RIPPLE: self._ripple_animation,
            AnimationType.RANDOM: self._random_animation,
            AnimationType.SPIRAL: self._spiral_animation,
            AnimationType.FIREWORK: self._firework_animation,
            AnimationType.PULSE: self._pulse_animation,
            AnimationType.COLOR_WIPE: self._color_wipe_animation,
            AnimationType.ENERGY_FIELD: self._energy_field_animation,
            AnimationType.BOUNCE: self._bounce_animation,
            AnimationType.SPARKLE: self._sparkle_animation,
            AnimationType.DNA: self._dna_helix_animation,
            AnimationType.CHASE: self._chase_animation,
            AnimationType.TETRIS: self._tetris_animation,
            AnimationType.LASER: self._laser_animation,
            AnimationType.GALAXY: self._galaxy_animation,
            AnimationType.PIANO: self._piano_animation,
            AnimationType.EQUALIZER: self._equalizer_animation,
        }
        
        animation_func = animations.get(animation_type)
        if animation_func:
            animation_func()

    def _rainbow_animation(self):
        """Regenbogen-Animation mit gleichmäßigen, weichen Farbübergängen"""
        # Farben in optimaler Reihenfolge für sanfte Übergänge
        colors = [
            PadColor.RED,      # #FF0000
            PadColor.ORANGE,   # #FF5400 
            PadColor.YELLOW,   # #FFFF00
            PadColor.GREEN,    # #00FF00
            PadColor.BLUE,     # #0000FF
        ]
        
        # Anzahl der Zwischenschritte pro Farbübergang
        steps = 6  # 6 Schritte zwischen jeder Farbe
        total_steps = steps * len(colors)
        
        offset = 0
        while self.animation_running:
            for row in range(8):
                for col in range(8):
                    # Position im Gesamtverlauf (0 bis total_steps)
                    pos = (col + row + offset) % total_steps
                    
                    # Bestimme die aktuelle Farbposition
                    color_pos = pos / steps
                    current_color_idx = int(color_pos)
                    
                    # Wähle Farbe basierend auf Position
                    color = colors[current_color_idx]
                    
                    # Berechne Helligkeit für den Übergang
                    step_in_transition = color_pos % 1
                    if step_in_transition < 0.33:
                        channel = 6  # 100% Helligkeit
                    elif step_in_transition < 0.66:
                        channel = 5  # 90% Helligkeit
                    else:
                        channel = 4  # 75% Helligkeit
                    
                    # Verwende _get_note für korrekte Orientierung
                    note = self._get_note(row, col)
                    self.set_pad_color(note, color, channel=channel)
            
            offset = (offset + 1) % total_steps
            time.sleep(0.08)

    def _wave_animation(self):
        """Verbesserte Wellenanimation mit mehreren Farben"""
        colors = [PadColor.BLUE, PadColor.GREEN, PadColor.YELLOW]
        wave_length = 12
        
        while self.animation_running:
            for offset in range(wave_length):
                for row in range(8):
                    for col in range(8):
                        # Berechne Wellenposition
                        pos = (col + row + offset) % wave_length
                        # Smooth sine wave
                        wave_val = math.sin(2 * math.pi * pos / wave_length)
                        
                        # Wähle Farbe basierend auf Position
                        color_idx = int((wave_val + 1) * len(colors) / 2)
                        color_idx = min(color_idx, len(colors) - 1)
                        
                        # Helligkeit basierend auf Wellenposition
                        brightness = int(6 * (wave_val + 1) / 2)
                        brightness = max(3, min(6, brightness))
                        
                        note = row * 8 + col
                        self.set_pad_color(note, colors[color_idx], channel=brightness)
                
                time.sleep(0.05)

    def _rain_animation(self):
        """Regen-Animation von oben nach unten"""
        while self.animation_running:
            # Zufällig Tropfen am oberen Rand erzeugen
            for _ in range(3):
                col = random.randint(0, 7)
                note = self._get_note(7, col)  # Start in oberster Reihe
                self.set_pad_color(note, PadColor.LIGHT_BLUE)
            
            # Alle Tropfen nach unten bewegen
            for row in range(7, 0, -1):  # Von oben nach unten
                for col in range(8):
                    current_note = self._get_note(row, col)
                    next_note = self._get_note(row-1, col)
                    
                    state_current = self.led_states.get(current_note, None)
                    if state_current and state_current.color != PadColor.OFF:
                        # Verblassen beim Fallen
                        channel = max(1, 6 - (7-row))
                        self.set_pad_color(next_note, PadColor.LIGHT_BLUE, channel=channel)
                        self.set_pad_color(current_note, PadColor.OFF)
            
            time.sleep(0.1)

    def _snake_animation(self):
        """Schlangen-Animation"""
        snake = [(0, 0)]
        direction = (0, 1)  # Start nach rechts
        
        while self.animation_running:
            # Kopf bewegen
            head = snake[-1]
            new_head = (head[0] + direction[0], head[1] + direction[1])
            
            # Richtung ändern wenn Wand erreicht
            if not (0 <= new_head[0] < 8 and 0 <= new_head[1] < 8):
                if direction == (0, 1):  # rechts
                    direction = (1, 0)  # runter
                elif direction == (1, 0):  # runter
                    direction = (0, -1)  # links
                elif direction == (0, -1):  # links
                    direction = (-1, 0)  # hoch
                else:  # hoch
                    direction = (0, 1)  # rechts
                continue
                
            snake.append(new_head)
            if len(snake) > 5:  # Schlangenlänge begrenzen
                snake.pop(0)
                
            # Schlange zeichnen
            self.clear_all()
            for i, pos in enumerate(snake):
                note = pos[0] * 8 + pos[1]
                color = PadColor.RED if i == len(snake)-1 else PadColor.DARK_RED
                self.set_pad_color(note, color)
                
            time.sleep(0.1)
            
    def _ripple_animation(self):
        """Wassertropfen-Animation"""
        center_x, center_y = 3.5, 3.5  # Mittelpunkt des Grids
        
        while self.animation_running:
            for radius in range(12):  # Größerer Radius für smootheren Übergang
                for row in range(8):
                    for col in range(8):
                        distance = math.sqrt((row - center_y)**2 + (col - center_x)**2)
                        wave = math.sin(distance - radius/2)
                        note = row * 8 + col
                        
                        if wave > 0.5:
                            color = PadColor.DARK_LIME
                        elif wave > 0:
                            color = PadColor.BLUE
                        elif wave > -0.5:
                            color = PadColor.DARK_BLUE
                        else:
                            color = PadColor.OFF
                            
                        self.set_pad_color(note, color)
                time.sleep(0.05)
                
    def _random_animation(self):
        """Zufällige Farbwechsel"""
        colors = [color for color in PadColor if color != PadColor.OFF]
        
        while self.animation_running:
            note = random.randint(0, 63)
            color = random.choice(colors)
            self.set_pad_color(note, color)
            time.sleep(0.05) 
        
    def _spiral_animation(self):
        """Spiralförmige Animation mit Farbverlauf"""
        colors = [PadColor.RED, PadColor.ORANGE, PadColor.YELLOW, PadColor.GREEN, PadColor.BLUE]
        center = (3.5, 3.5)
        angle = 0
        
        while self.animation_running:
            # Reduziere die Anzahl der Winkel-Schritte für schnellere Animation
            angle = (angle + 6) % 360  # Größere Schritte (6 statt 1)
            
            for row in range(8):
                for col in range(8):
                    # Berechne Abstand zum Zentrum und Winkel
                    dx = col - center[0]
                    dy = row - center[1]
                    distance = math.sqrt(dx*dx + dy*dy)
                    theta = math.atan2(dy, dx) * 180 / math.pi
                    
                    # Farbauswahl basierend auf Winkel und Abstand
                    color_idx = int(((theta + angle) % 360) * len(colors) / 360)
                    
                    # Helligkeit basierend auf Abstand
                    brightness = 6 - min(int(distance), 3)
                    
                    note = row * 8 + col
                    # Prüfe ob Animation noch läuft bevor LED gesetzt wird
                    if not self.animation_running:
                        return
                    self.set_pad_color(note, colors[color_idx], channel=brightness)
            
            # Schnellere Aktualisierung
            time.sleep(0.01)

    def _firework_animation(self):
        """Feuerwerks-Animation mit Explosionen"""
        while self.animation_running:
            # Startposition am unteren Rand
            start_col = random.randint(0, 7)
            color = random.choice([PadColor.RED, PadColor.BLUE, PadColor.GREEN, PadColor.YELLOW])
            
            # Aufstieg
            for row in range(8):  # Von unten nach oben
                note = self._get_note(row, start_col)
                self.set_pad_color(note, color, channel=6)
                time.sleep(0.05)
                self.set_pad_color(note, PadColor.OFF)
            
            # Explosion
            center_row = random.randint(4, 7)  # Explosion im oberen Bereich
            center_col = start_col
            
            for radius in range(5):
                # Zeichne Explosionsring
                for row in range(max(0, center_row-radius), min(8, center_row+radius+1)):
                    for col in range(max(0, center_col-radius), min(8, center_col+radius+1)):
                        if abs(row-center_row) + abs(col-center_col) == radius:
                            note = self._get_note(row, col)
                            self.set_pad_color(note, color, channel=6-radius)
                
                time.sleep(0.05)
            
            # Verblassen
            time.sleep(0.2)
            self.clear_all()
            time.sleep(0.3)

    def switch_channel(self):
        """Wechselt zwischen Kanal 1 und Kanal 7"""
        self.channel = 6 if self.channel == 0 else 0  # 0 für Kanal 1, 6 für Kanal 7
        print(f"Jetzt auf Kanal {'7' if self.channel == 6 else '1'}")  # Debug-Ausgabe 

    def _pulse_animation(self):
        """Pulsierender Effekt über das gesamte Grid"""
        colors = [PadColor.RED, PadColor.BLUE, PadColor.GREEN]
        
        while self.animation_running:
            for brightness in range(0, 7):  # Aufhellen
                for note in range(64):
                    color = colors[note % len(colors)]
                    self.set_pad_color(note, color, channel=brightness)
                time.sleep(0.05)
            
            for brightness in range(6, -1, -1):  # Abdunkeln
                for note in range(64):
                    color = colors[note % len(colors)]
                    self.set_pad_color(note, color, channel=brightness)
                time.sleep(0.05)

    def _color_wipe_animation(self):
        """Farbwischer-Animation"""
        colors = [PadColor.RED, PadColor.YELLOW, PadColor.GREEN, PadColor.BLUE]
        
        while self.animation_running:
            for color in colors:
                # Von links nach rechts
                for col in range(8):
                    # Prüfe ob Animation noch läuft
                    if not self.animation_running:
                        return
                        
                    for row in range(8):
                        note = self._get_note(row, col)
                        self.set_pad_color(note, color, channel=6)
                    time.sleep(0.05)
                
                # Prüfe nochmal vor der Pause zwischen den Farben
                if not self.animation_running:
                    return
                time.sleep(0.1)

    def _energy_field_animation(self):
        """Energiefeld-Animation mit pulsierenden Energielinien"""
        colors = [PadColor.BLUE, PadColor.LIGHT_BLUE, PadColor.GREEN, PadColor.LIGHT_GREEN]
        energy_points = [(random.randint(0, 7), random.randint(0, 7)) for _ in range(3)]
        time_offset = 0
        
        while self.animation_running:
            for row in range(8):
                for col in range(8):
                    # Berechne Energielevel basierend auf Abstand zu Energiepunkten
                    energy = 0
                    for point_x, point_y in energy_points:
                        distance = math.sqrt((row - point_y)**2 + (col - point_x)**2)
                        # Pulsierende Energie mit Sinus
                        energy += math.sin(distance + time_offset) / (distance + 1)
                    
                    # Normalisiere Energie und wähle Farbe
                    energy = (energy + 3) / 6  # Normalisiere auf 0-1
                    color_idx = min(int(energy * len(colors)), len(colors) - 1)
                    
                    # Helligkeit basierend auf Energielevel
                    brightness = min(6, max(3, int(energy * 6)))
                    
                    note = self._get_note(row, col)
                    self.set_pad_color(note, colors[color_idx], channel=brightness)
            
            # Bewege Energiepunkte langsam
            energy_points = [(x + random.uniform(-0.1, 0.1), y + random.uniform(-0.1, 0.1)) 
                           for x, y in energy_points]
            energy_points = [(max(0, min(7, x)), max(0, min(7, y))) 
                           for x, y in energy_points]
            
            time_offset += 0.2
            time.sleep(0.05)

    def _dna_helix_animation(self):
        """DNA-Helix Animation mit zwei sich windenden Strängen"""
        colors = [PadColor.RED, PadColor.BLUE]  # Zwei DNA-Stränge
        wave_height = 4  # Amplitude der Welle
        wave_length = 12  # Länge einer kompletten Welle
        offset = 0
        
        while self.animation_running:
            # Lösche vorherigen Frame
            for note in range(64):
                self.set_pad_color(note, PadColor.OFF)
            
            # Zeichne beide DNA-Stränge
            for strand in range(2):
                phase_offset = math.pi * strand  # Versatz zwischen den Strängen
                
                # Zeichne den Strang
                for x in range(16):  # Überlappende Punkte für Smoothness
                    # Berechne y-Position der Helix
                    y = wave_height * math.sin((x / wave_length) * 2 * math.pi + 
                                             offset + phase_offset)
                    
                    # Projiziere auf 8x8 Grid
                    grid_x = int(x / 2) % 8
                    grid_y = int(3.5 + y)
                    
                    if 0 <= grid_y < 8:
                        note = self._get_note(grid_y, grid_x)
                        # Helligkeit basierend auf Position im Strang
                        brightness = 4 + int(2 * abs(math.sin(x / 4)))
                        self.set_pad_color(note, colors[strand], channel=brightness)
                        
                        # Zeichne "Verbindungen" zwischen den Strängen
                        if strand == 0 and x % 4 == 0:
                            connection_y = int(3.5 - y/2)
                            if 0 <= connection_y < 8:
                                note = self._get_note(connection_y, grid_x)
                                self.set_pad_color(note, PadColor.YELLOW, channel=5)
            
            offset += 0.2
            time.sleep(0.05)

    def _tetris_animation(self):
        """Tetris-ähnliche Animation mit fallenden Blöcken"""
        colors = [PadColor.RED, PadColor.BLUE, PadColor.GREEN, PadColor.YELLOW]
        
        while self.animation_running:
            # Neuer Block am oberen Rand
            block_width = random.randint(2, 4)
            start_col = random.randint(0, 8-block_width)
            color = random.choice(colors)
            
            # Block fallen lassen
            for row in range(8):
                # Block zeichnen
                for col in range(start_col, start_col + block_width):
                    note = self._get_note(7-row, col)
                    self.set_pad_color(note, color, channel=6)
                
                time.sleep(0.1)
                
                # Block löschen
                if row < 7:  # Nicht löschen in der letzten Reihe
                    for col in range(start_col, start_col + block_width):
                        note = self._get_note(7-row, col)
                        self.set_pad_color(note, PadColor.OFF)
            
            time.sleep(0.2)

    def _laser_animation(self):
        """Laser-Schuss Animation mit Auflade-Effekt"""
        while self.animation_running:
            # Zufällige Startposition
            start_col = random.randint(0, 7)
            
            # Aufladen (pulsierend)
            for charge in range(5):
                note = self._get_note(0, start_col)
                self.set_pad_color(note, PadColor.RED, channel=3 + charge)
                time.sleep(0.1)
            
            # Laser-Schuss
            for row in range(8):
                # Strahl
                note = self._get_note(row, start_col)
                self.set_pad_color(note, PadColor.RED, channel=6)
                
                # Seitliche Energie
                if start_col > 0:
                    side_note = self._get_note(row, start_col-1)
                    self.set_pad_color(side_note, PadColor.ORANGE, channel=4)
                if start_col < 7:
                    side_note = self._get_note(row, start_col+1)
                    self.set_pad_color(side_note, PadColor.ORANGE, channel=4)
                
                time.sleep(0.03)
            
            # Aufräumen
            time.sleep(0.1)
            self.clear_all()
            time.sleep(0.2)

    def _galaxy_animation(self):
        """Galaxie-Animation mit rotierenden Sternen"""
        center = (3.5, 3.5)
        stars = [(random.uniform(0, 7), random.uniform(0, 7)) for _ in range(10)]
        angles = [random.uniform(0, 2*math.pi) for _ in range(10)]
        speeds = [random.uniform(0.02, 0.06) for _ in range(10)]  # Reduzierte Geschwindigkeiten
        
        while self.animation_running:
            # Lösche vorherigen Frame
            self.clear_all()
            
            # Aktualisiere und zeichne Sterne
            for i in range(len(stars)):
                # Berechne neue Position
                radius = math.sqrt((stars[i][0] - center[0])**2 + 
                                 (stars[i][1] - center[1])**2)
                angles[i] += speeds[i] / (radius + 0.5)  # Äußere Sterne langsamer
                
                x = center[0] + radius * math.cos(angles[i])
                y = center[1] + radius * math.sin(angles[i])
                
                # Zeichne Stern wenn im Grid
                if 0 <= x < 8 and 0 <= y < 8:
                    note = self._get_note(int(y), int(x))
                    brightness = 6 - min(int(radius), 3)
                    color = PadColor.WHITE if radius < 2 else PadColor.YELLOW
                    self.set_pad_color(note, color, channel=brightness)
            
            time.sleep(0.1)  # Erhöht von 0.05 auf 0.1

    def _piano_animation(self):
        """Piano-Tasten Animation"""
        while self.animation_running:
            # Zufällige "Taste" auswählen
            col = random.randint(0, 7)
            
            # Taste drücken (von unten nach oben)
            for row in range(8):
                note = self._get_note(row, col)
                if col % 2 == 0:  # "Weiße" Tasten
                    self.set_pad_color(note, PadColor.WHITE, channel=6)
                else:  # "Schwarze" Tasten
                    self.set_pad_color(note, PadColor.BLUE, channel=6)
                time.sleep(0.02)
            
            # Taste loslassen (von oben nach unten)
            for row in range(7, -1, -1):
                note = self._get_note(row, col)
                if col % 2 == 0:
                    self.set_pad_color(note, PadColor.WHITE, channel=3)
                else:
                    self.set_pad_color(note, PadColor.BLUE, channel=3)
                time.sleep(0.02)
            
            # Kurze Pause zwischen den Tasten
            time.sleep(0.1)

    def _equalizer_animation(self):
        """Audio Equalizer Animation"""
        levels = [0] * 8  # Pegel für jede Spalte
        target_levels = [0] * 8
        
        while self.animation_running:
            # Neue Ziel-Level generieren
            for i in range(8):
                if random.random() < 0.3:  # 30% Chance für Änderung
                    target_levels[i] = random.randint(0, 7)
            
            # Level smooth anpassen
            for col in range(8):
                if levels[col] < target_levels[col]:
                    levels[col] = min(levels[col] + 1, 7)
                elif levels[col] > target_levels[col]:
                    levels[col] = max(levels[col] - 1, 0)
                
                # Spalte zeichnen
                for row in range(8):
                    note = self._get_note(row, col)
                    if row <= levels[col]:
                        # Farbe basierend auf Höhe
                        if row < 3:
                            color = PadColor.GREEN
                        elif row < 5:
                            color = PadColor.YELLOW
                        else:
                            color = PadColor.RED
                        self.set_pad_color(note, color, channel=6)
                    else:
                        self.set_pad_color(note, PadColor.OFF)
            
            time.sleep(0.05)

    def _bounce_animation(self):
        """Springender Ball-Effekt"""
        pos_x = random.randint(0, 7)
        pos_y = 0
        dx = 1
        dy = 0
        gravity = 0.2
        velocity = 0
        
        while self.animation_running:
            # Alten Position löschen
            old_note = int(pos_y) * 8 + int(pos_x)
            if 0 <= old_note < 64:
                self.set_pad_color(old_note, PadColor.OFF)
            
            # Physik berechnen
            velocity += gravity
            pos_y += velocity
            pos_x += dx
            
            # Kollisionen prüfen
            if pos_y >= 7:
                pos_y = 7
                velocity = -velocity * 0.8  # Bounce mit Energieverlust
            
            if pos_x >= 7 or pos_x <= 0:
                dx = -dx  # Richtungswechsel an den Wänden
                pos_x = max(0, min(7, pos_x))
            
            # Neue Position zeichnen
            new_note = int(pos_y) * 8 + int(pos_x)
            if 0 <= new_note < 64:
                self.set_pad_color(new_note, PadColor.YELLOW, channel=6)
            
            time.sleep(0.05)

    def _sparkle_animation(self):
        """Funkelnder Sternenhimmel-Effekt"""
        while self.animation_running:
            # Zufällige Funken erzeugen
            for _ in range(3):  # Reduziert von 5 auf 3 Funken pro Frame
                note = random.randint(0, 63)
                color = random.choice([PadColor.WHITE, PadColor.YELLOW])
                self.set_pad_color(note, color, channel=6)
            
            time.sleep(0.15)  # Erhöht von 0.05 auf 0.15
            
            # Funken verblassen lassen
            for note in range(64):
                if note in self.led_states:
                    self.set_pad_color(note, PadColor.OFF)

    def _chase_animation(self):
        """Verfolgungsjagd-Animation"""
        head_pos = 0
        tail_length = 5
        color = random.choice([PadColor.RED, PadColor.BLUE, PadColor.GREEN])
        
        while self.animation_running:
            # Kopf der Schlange bewegen
            for i in range(tail_length):
                pos = (head_pos - i) % 64
                if pos >= 0:
                    brightness = 6 - i  # Helligkeit nimmt zum Schwanz hin ab
                    self.set_pad_color(pos, color, channel=max(1, brightness))
            
            # Alte Position löschen
            old_pos = (head_pos - tail_length) % 64
            if old_pos >= 0:
                self.set_pad_color(old_pos, PadColor.OFF)
            
            head_pos = (head_pos + 1) % 64
            time.sleep(0.05) 

    def _get_note(self, row: int, col: int) -> int:
        """
        Konvertiert row/col Position zu MIDI-Note, von unten nach oben zählend
        row: 0 ist unten, 7 ist oben
        col: 0 ist links, 7 ist rechts
        """
        return row * 8 + col  # Einfache Umrechnung, da 0 jetzt unten ist

    def _get_row_col(self, note: int) -> tuple[int, int]:
        """
        Konvertiert MIDI-Note zu row/col Position, von unten nach oben zählend
        Returns: (row, col) wobei row 0 unten ist
        """
        col = note % 8
        row = note // 8  # Keine Umkehrung mehr nötig
        return row, col 