# APC mini mk2 Controller Software

![Logo](src/logo.png)

A powerful and feature-rich control software for the AKAI APC mini mk2 MIDI controller, developed with significant assistance from AI (Claude).

## 🚨 Important Notice

This software was developed in collaboration with AI (specifically Claude by Anthropic). While this enabled rapid development and sophisticated features, it's important to acknowledge the AI's contribution.

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

This software is designed to enhance the capabilities of the AKAI APC mini mk2 MIDI controller, transforming it from a simple MIDI controller into a versatile performance and visual tool. It's particularly useful for:

- Live performance lighting control
- Visual music accompaniment
- Interactive installations
- MIDI-based light shows
- Custom controller configurations
- Educational demonstrations
- Visual effect programming

## 💻 Requirements
- Python 3.8+
- PyQt6
- mido
- rtmidi
- AKAI APC mini mk2 controller

## 🚀 Getting Started

1. Connect your APC mini mk2
2. Install dependencies:
