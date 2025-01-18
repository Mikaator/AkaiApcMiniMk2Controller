from led_controller import LedController, Color
import time

def main():
    # Ersetze 'APC mini mk2' durch den tatsächlichen Namen deines Geräts
    controller = LedController('APC mini mk2')
    
    # Alle LEDs ausschalten
    controller.clear_all()
    
    # Ein paar Beispiel-Patterns
    for note in range(64):  # Die ersten 64 Buttons sind die Haupt-Grid
        controller.set_led_color(note, Color.RED)
        time.sleep(0.05)  # Kleine Verzögerung für einen visuellen Effekt
        
    time.sleep(1)
    controller.clear_all()

if __name__ == "__main__":
    main() 