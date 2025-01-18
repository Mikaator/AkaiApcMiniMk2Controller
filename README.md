# APC mini mk2 Controller Software

![Logo](midiakaicontroller/logo.png)

A powerful and feature-rich control software for the AKAI APC mini mk2 MIDI controller to enhance usabillity with dot2 on PC or other Lighting Software. 

## 🚨 Important Notice

This software was developed in collaboration with AI. While this enabled rapid development and sophisticated features, it's important to acknowledge the AI's contribution.

## ⚖️ Copyright and License

Copyright © 2024 Mikaator (michatfragen@gmail.com)

This software is protected under a custom license:
- You are free to use, modify and study this software for personal use
- Commercial use is prohibited without explicit permission
- You must maintain all copyright notices and attributions
- You may not claim this work as your own
- Redistributions must include this copyright notice and AI contribution acknowledgment

## 🎛️ Features

### LED Control
- Full RGB color control for the 8x8 grid
- Adjustable brightness levels (10% to 100%)
- Dynamic animations including:
  - Pulsing (1/16 to 1/2 speed)
  - Blinking (1/24 to 1/2 speed)
  - Static colors

### Button Behaviors
- Two operation modes:
  - Toggle Mode: Press to switch between states
  - Flash Mode: Temporary state change while pressed
- Individual button configuration:
  - Custom colors for pressed/unpressed states
  - Independent animation settings
  - Adjustable brightness levels

### Animations
- 15+ built-in animations including:
  - Rainbow waves
  - Color wipes
  - Matrix rain effect
  - Fireworks
  - DNA helix
  - Galaxy simulation
  - Piano visualization
  - Audio equalizer simulation
  - Tetris-style effects
  - Laser shows
  - And more...

### Configuration
- Save/Load complete button configurations
- MIDI device management with loopback support
- Dark/Light theme support
- Multi-language support (English/German)

## 🔧 Technical Features
- Real-time MIDI communication
- Multi-threaded animation engine
- Event-driven button handling
- Configurable MIDI routing
- Modern PyQt6-based GUI
- Extensible animation framework

## 🎯 Purpose

- Live performance lighting control
- Visual music accompaniment
- Interactive installations
- MIDI-based light shows
- Custom controller configurations
- Educational demonstrations
- Visual effect programming
- -dot2 on Pc
- Grand MA 


🎛️ AKAI APC mini mk2 Controller Software - Installation & Usage Guide
===============================================================

📋 REQUIREMENTS
-----------
| Component       | Version/Specification |
|-----------------|----------------------|
| Python          | 3.8 or newer         |
| PyQt6          | ≥ 6.4.0              |
| mido           | ≥ 1.2.10             |
| python-rtmidi  | ≥ 1.4.9              |
| pathlib        | ≥ 1.0.1              |
| Hardware       | AKAI APC mini mk2     |
| Connection     | USB                   |

📥 INSTALLATION
-----------
1. Download and extract the software
2. Install required Python packages:
   pip install -r requirements.txt

🚀 RUNNING THE SOFTWARE
-------------------
1. Connect AKAI APC mini mk2 to your computer via USB
2. Start the software:
  cd "yourpath/to/dashboard.py" --> python dashboard.py
3. In the software interface:
   - Select AKAI APC mini mk2 from MIDI Input dropdown
   - Select AKAI APC mini mk2 from MIDI Output dropdown
   - Click "Connect"
   - LED grid should now be active and ready

💡 COMMON ISSUES
------------
- Python package installation fails:
  > pip install --upgrade pip
  > pip install -r requirements.txt

- MIDI device not visible:
  > Disconnect and reconnect USB cable
  > Check device manager/system settings
  
- LED grid not responding:
  > Ensure no other software is using the MIDI device
  > Try selecting different MIDI ports
  > Restart the software

📞 SUPPORT
-------
For assistance contact: michatfragen@gmail.com
