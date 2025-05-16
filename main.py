import sys
import pygame
import time
from chip8.constants import VIDEO_HEIGHT, VIDEO_WIDTH
from chip8.chip8 import Chip8
from chip8.platform import Platform

def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <Scale> <Delay> <ROM>")
        sys.exit(1)

    video_scale = int(sys.argv[1])
    cycle_delay = int(sys.argv[2])
    rom_filename = sys.argv[3]

    platform = Platform("CHIP-8 Emulator", VIDEO_WIDTH * video_scale, VIDEO_HEIGHT * video_scale, VIDEO_WIDTH, VIDEO_HEIGHT)
    chip8 = Chip8()
    chip8.load_rom(rom_filename)

    last_cycle_time = time.time()
    quit_game = False

    while not quit_game:
        quit_game = platform.process_input(chip8.keypad)
        print("keypad:",chip8.keypad)
        current_time = time.time()
        dt = (current_time - last_cycle_time) * 1000  # ms
        chip8.cycle()
        platform.update(chip8.video)

    
    pygame.quit()

if __name__ == "__main__":
    main()