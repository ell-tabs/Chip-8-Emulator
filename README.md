# Chip-8-Emulator

This is a simple Chip-8 emulator written in Python. It implements the Chip-8 virtual machine, including its opcode set, memory, display, keypad, and timers.

## Features

- Supports all standard Chip-8 opcodes
- 64x32 pixel monochrome display
- Keyboard input handling
- Delay and sound timers
- Modular codebase with separate files for constants, opcodes, platform abstraction, and the main Chip-8 class

## File Structure

- `chip8.py` - Main Chip8 class and emulator logic
- `constants.py` - Shared constants used across the project
- `opcodes.py` - Opcode implementations
- `platform.py` - Platform-specific code (e.g., display and input handling)

## Installation

Make sure you have Python 3.8+ installed.

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Running a program

Insert your .ch8 file into /ROMS folder

input this into the terminal:

# EXAMPLE

```bash
python 10 16 game.ch8 # scaleVal, DelayTime, File.ch8
```