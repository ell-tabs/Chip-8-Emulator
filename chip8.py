import random
import pygame
import numpy as np
import time
import sys

VIDEO_WIDTH = 64
VIDEO_HEIGHT = 32
START_ADDRESS = 0x200
FONTSET_SIZE = 80
FONTSET_START_ADDRESS = 0x50

fontset = [
    0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
    0x20, 0x60, 0x20, 0x20, 0x70, # 1
    0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
    0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
    0x90, 0x90, 0xF0, 0x10, 0x10, # 4
    0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
    0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
    0xF0, 0x10, 0x20, 0x40, 0x40, # 7
    0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
    0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
    0xF0, 0x90, 0xF0, 0x90, 0x90, # A
    0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
    0xF0, 0x80, 0x80, 0x80, 0xF0, # C
    0xE0, 0x90, 0x90, 0x90, 0xE0, # D
    0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
    0xF0, 0x80, 0xF0, 0x80, 0x80  # F
]

class Chip8:
    def __init__(self):
        self.registers = [0] * 16
        self.memory = [0] * 4096
        self.index = 0
        self.pc = START_ADDRESS
        self.stack = [0] * 16
        self.sp = 0
        self.delayTimer = 0
        self.soundTimer = 0
        self.keypad = [0] * 16
        self.video = np.zeros((VIDEO_HEIGHT, VIDEO_WIDTH), dtype=np.uint8)
        self.opcode = 0

        self.randGen = random.Random(int(time.time()))

        for i in range(FONTSET_SIZE):
            self.memory[FONTSET_START_ADDRESS + i] = fontset[i]

        self.table = {
            0x0: self.Table0,
            0x1: self.OP_1nnn,
            0x2: self.OP_2nnn,
            0x3: self.OP_3xkk,
            0x4: self.OP_4xkk,
            0x5: self.OP_5xy0,
            0x6: self.OP_6xkk,
            0x7: self.OP_7xkk,
            0x8: self.Table8,
            0x9: self.OP_9xy0,
            0xA: self.OP_Annn,
            0xB: self.OP_Bnnn,
            0xC: self.OP_Cxkk,
            0xD: self.OP_Dxyn,
            0xE: self.TableE,
            0xF: self.TableF,
        }

        self.table0 = {
            0x00E0: self.OP_00E0,
            0x00EE: self.OP_00EE,
        }

        self.table8 = {
            0x0: self.OP_8xy0,
            0x1: self.OP_8xy1,
            0x2: self.OP_8xy2,
            0x3: self.OP_8xy3,
            0x4: self.OP_8xy4,
            0x5: self.OP_8xy5,
            0x6: self.OP_8xy6,
            0x7: self.OP_8xy7,
            0xE: self.OP_8xyE,
        }

        self.tableE = {
            0x1: self.OP_ExA1,
            0xE: self.OP_Ex9E,
        }

        self.tableF = {
            0x07: self.OP_Fx07,
            0x0A: self.OP_Fx0A,
            0x15: self.OP_Fx15,
            0x18: self.OP_Fx18,
            0x1E: self.OP_Fx1E,
            0x29: self.OP_Fx29,
            0x33: self.OP_Fx33,
            0x55: self.OP_Fx55,
            0x65: self.OP_Fx65,
        }

    def Table8(self):
        code = self.opcode & 0x000F
        if code in self.table8:
            self.table8[code]()

    def Table0(self):
        code = self.opcode & 0x00FF
        if code in self.table0:
            self.table0[code]()

    def TableE(self):
        code = self.opcode & 0x000F
        if code in self.tableE:
            self.tableE[code]()

    def TableF(self):
        code = self.opcode & 0x00FF
        if code in self.tableF:
            self.tableF[code]()

    def cycle(self):
        self.opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
        prev_pc = self.pc
        self.table[(self.opcode & 0xF000) >> 12]()
        # If opcode didn't change PC, advance it by 2
        if self.pc == prev_pc:
            self.pc += 2

    def update_timers(self):
        if self.delayTimer > 0:
            self.delayTimer -= 1
        if self.soundTimer > 0:
            self.soundTimer -= 1

    def load_rom(self, filename):
        try:
            with open(filename, 'rb') as file:
                rom_data = file.read()
                for i in range(len(rom_data)):
                    self.memory[START_ADDRESS + i] = rom_data[i] & 0xFF
        except IOError as e:
            print(f"Error Loading ROM: {e}")

    def random_byte(self):
        return self.randGen.randint(0, 255)

    # --- OPCODES --- #
    def OP_00E0(self):
        self.video.fill(0)
        self.pc += 2

    def OP_00EE(self):
        if self.sp > 0:
            self.sp -= 1
            self.pc = self.stack[self.sp]
        else:
            self.pc = START_ADDRESS

    def OP_1nnn(self):
        address = self.opcode & 0x0FFF
        self.pc = address

    def OP_2nnn(self):
        address = self.opcode & 0x0FFF
        if self.sp < len(self.stack):
            self.stack[self.sp] = self.pc + 2
            self.sp += 1
            self.pc = address
        else:
            print("[2NNN] ERROR: Stack overflow — unable to push return address.")

    def OP_3xkk(self):
        Vx = (self.opcode & 0x0F00) >> 8
        byte = self.opcode & 0x00FF
        if self.registers[Vx] == byte:
            self.pc += 4
        else:
            self.pc += 2

    def OP_4xkk(self):
        Vx = (self.opcode & 0x0F00) >> 8
        byte = self.opcode & 0x00FF
        if self.registers[Vx] != byte:
            self.pc += 4
        else:
            self.pc += 2

    def OP_5xy0(self):
        Vx = (self.opcode & 0x0F00) >> 8
        Vy = (self.opcode & 0x00F0) >> 4
        if self.registers[Vx] == self.registers[Vy]:
            self.pc += 4
        else:
            self.pc += 2

    def OP_6xkk(self):
        Vx = (self.opcode & 0x0F00) >> 8
        byte = self.opcode & 0x00FF
        self.registers[Vx] = byte
        self.pc += 2

    def OP_7xkk(self):
        Vx = (self.opcode & 0x0F00) >> 8
        byte = self.opcode & 0x00FF
        self.registers[Vx] = (self.registers[Vx] + byte) & 0xFF
        self.pc += 2

    def OP_8xy0(self):
        Vx = (self.opcode & 0x0F00) >> 8
        Vy = (self.opcode & 0x00F0) >> 4
        self.registers[Vx] = self.registers[Vy]
        self.pc += 2

    def OP_8xy1(self):
        Vx = (self.opcode & 0x0F00) >> 8
        Vy = (self.opcode & 0x00F0) >> 4
        self.registers[Vx] |= self.registers[Vy]
        self.pc += 2

    def OP_8xy2(self):
        Vx = (self.opcode & 0x0F00) >> 8
        Vy = (self.opcode & 0x00F0) >> 4
        self.registers[Vx] &= self.registers[Vy]
        self.pc += 2

    def OP_8xy3(self):
        Vx = (self.opcode & 0x0F00) >> 8
        Vy = (self.opcode & 0x00F0) >> 4
        self.registers[Vx] ^= self.registers[Vy]
        self.pc += 2

    def OP_8xy4(self):
        Vx = (self.opcode & 0x0F00) >> 8
        Vy = (self.opcode & 0x00F0) >> 4
        sum_val = self.registers[Vx] + self.registers[Vy]
        self.registers[0xF] = 1 if sum_val > 0xFF else 0
        self.registers[Vx] = sum_val & 0xFF
        self.pc += 2

    def OP_8xy5(self):
        Vx = (self.opcode & 0x0F00) >> 8
        Vy = (self.opcode & 0x00F0) >> 4
        self.registers[0xF] = 1 if self.registers[Vx] > self.registers[Vy] else 0
        self.registers[Vx] = (self.registers[Vx] - self.registers[Vy]) & 0xFF
        self.pc += 2

    def OP_8xy6(self):
        Vx = (self.opcode & 0x0F00) >> 8
        self.registers[0xF] = self.registers[Vx] & 0x1
        self.registers[Vx] >>= 1
        self.pc += 2

    def OP_8xy7(self):
        Vx = (self.opcode & 0x0F00) >> 8
        Vy = (self.opcode & 0x00F0) >> 4
        self.registers[0xF] = 1 if self.registers[Vy] > self.registers[Vx] else 0
        self.registers[Vx] = (self.registers[Vy] - self.registers[Vx]) & 0xFF
        self.pc += 2

    def OP_8xyE(self):
        Vx = (self.opcode & 0x0F00) >> 8
        self.registers[0xF] = (self.registers[Vx] & 0x80) >> 7
        self.registers[Vx] = (self.registers[Vx] << 1) & 0xFF
        self.pc += 2

    def OP_9xy0(self):
        Vx = (self.opcode & 0x0F00) >> 8
        Vy = (self.opcode & 0x00F0) >> 4
        if self.registers[Vx] != self.registers[Vy]:
            self.pc += 4
        else:
            self.pc += 2

    def OP_Annn(self):
        address = self.opcode & 0x0FFF
        self.index = address
        self.pc += 2

    def OP_Bnnn(self):
        address = self.opcode & 0x0FFF
        self.pc = self.registers[0] + address

    def OP_Cxkk(self):
        Vx = (self.opcode & 0x0F00) >> 8
        byte = self.opcode & 0x00FF
        self.registers[Vx] = self.random_byte() & byte
        self.pc += 2

    def OP_Dxyn(self):
        Vx = (self.opcode & 0x0F00) >> 8
        Vy = (self.opcode & 0x00F0) >> 4
        height = self.opcode & 0x000F
        xPos = self.registers[Vx] % VIDEO_WIDTH
        yPos = self.registers[Vy] % VIDEO_HEIGHT
        self.registers[0xF] = 0

        for row in range(height):
            spriteByte = self.memory[self.index + row]
            for col in range(8):
                mask = 0x80 >> col
                spritePixel = (spriteByte & mask) != 0
                screenX = (xPos + col) % VIDEO_WIDTH
                screenY = (yPos + row) % VIDEO_HEIGHT
                if spritePixel:
                    if self.video[screenY, screenX]:
                        self.registers[0xF] = 1
                    self.video[screenY, screenX] ^= 1
        self.pc += 2

    def OP_Ex9E(self):
        Vx = (self.opcode & 0x0F00) >> 8
        key = self.registers[Vx]
        if self.keypad[key]:
            self.pc += 4
        else:
            self.pc += 2

    def OP_ExA1(self):
        Vx = (self.opcode & 0x0F00) >> 8
        key = self.registers[Vx]
        if not self.keypad[key]:
            self.pc += 4
        else:
            self.pc += 2

    def OP_Fx07(self):
        Vx = (self.opcode & 0x0F00) >> 8
        self.registers[Vx] = self.delayTimer
        self.pc += 2

    def OP_Fx0A(self):
        Vx = (self.opcode & 0x0F00) >> 8
        for i in range(16):
            if self.keypad[i]:
                self.registers[Vx] = i
                self.pc += 2
                return
        # If no key pressed, do not increment PC

    def OP_Fx15(self):
        Vx = (self.opcode & 0x0F00) >> 8
        self.delayTimer = self.registers[Vx]
        self.pc += 2

    def OP_Fx18(self):
        Vx = (self.opcode & 0x0F00) >> 8
        self.soundTimer = self.registers[Vx]
        self.pc += 2

    def OP_Fx1E(self):
        Vx = (self.opcode & 0x0F00) >> 8
        self.index = (self.index + self.registers[Vx]) & 0xFFFF
        self.pc += 2

    def OP_Fx29(self):
        Vx = (self.opcode & 0x0F00) >> 8
        digit = self.registers[Vx]
        self.index = FONTSET_START_ADDRESS + (5 * digit)
        self.pc += 2

    def OP_Fx33(self):
        Vx = (self.opcode & 0x0F00) >> 8
        value = self.registers[Vx]
        self.memory[self.index + 2] = value % 10
        value //= 10
        self.memory[self.index + 1] = value % 10
        value //= 10
        self.memory[self.index] = value % 10
        self.pc += 2

    def OP_Fx55(self):
        Vx = (self.opcode & 0x0F00) >> 8
        for i in range(Vx + 1):
            self.memory[self.index + i] = self.registers[i]
        self.pc += 2

    def OP_Fx65(self):
        Vx = (self.opcode & 0x0F00) >> 8
        for i in range(Vx + 1):
            self.registers[i] = self.memory[self.index + i]
        self.pc += 2

# --- RENDER --- #

class Platform:
    def __init__(self, title, window_width, window_height, texture_width, texture_height):
        pygame.init()
        self.window = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption(title)
        self.texture_width = texture_width
        self.texture_height = texture_height

    def update(self, buffer):
        rgb_array = np.stack([buffer * 255]*3, axis=2).astype(np.uint8)
        rgb_array = np.transpose(rgb_array, (1, 0, 2))  # swap height & width axes
        surf = pygame.surfarray.make_surface(rgb_array)
        surf = pygame.transform.scale(surf, (self.window.get_width(), self.window.get_height()))
        self.window.fill((0, 0, 0))
        self.window.blit(surf, (0, 0))
        pygame.display.flip()

    def process_input(self, keys):
        quit_game = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    quit_game = True
                self.handle_keydown(event.key, keys)
            elif event.type == pygame.KEYUP:
                self.handle_keyup(event.key, keys)
        return quit_game

    def handle_keydown(self, key, keys):
        key_mapping = {
            pygame.K_x: 0,
            pygame.K_1: 1,
            pygame.K_2: 2,
            pygame.K_3: 3,
            pygame.K_q: 4,
            pygame.K_w: 5,
            pygame.K_e: 6,
            pygame.K_a: 7,
            pygame.K_s: 8,
            pygame.K_d: 9,
            pygame.K_z: 0xA,
            pygame.K_c: 0xB,
            pygame.K_4: 0xC,
            pygame.K_r: 0xD,
            pygame.K_f: 0xE,
            pygame.K_v: 0xF,
        }
        if key in key_mapping:
            keys[key_mapping[key]] = 1

    def handle_keyup(self, key, keys):
        key_mapping = {
            pygame.K_x: 0,
            pygame.K_1: 1,
            pygame.K_2: 2,
            pygame.K_3: 3,
            pygame.K_q: 4,
            pygame.K_w: 5,
            pygame.K_e: 6,
            pygame.K_a: 7,
            pygame.K_s: 8,
            pygame.K_d: 9,
            pygame.K_z: 0xA,
            pygame.K_c: 0xB,
            pygame.K_4: 0xC,
            pygame.K_r: 0xD,
            pygame.K_f: 0xE,
            pygame.K_v: 0xF,
        }
        if key in key_mapping:
            keys[key_mapping[key]] = 0

# --- EXECUTE --- #

def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <Scale> <CyclesPerFrame> <ROM>")
        sys.exit(1)

    video_scale = int(sys.argv[1])
    cycles_per_frame = int(sys.argv[2])   # cycles per 1/60th sec (try 10-20 for accuracy, 100 for speed)
    rom_filename = sys.argv[3]

    platform = Platform(
        "CHIP-8 Emulator",
        VIDEO_WIDTH * video_scale,
        VIDEO_HEIGHT * video_scale,
        VIDEO_WIDTH,
        VIDEO_HEIGHT
    )
    chip8 = Chip8()
    chip8.load_rom(rom_filename)

    clock = pygame.time.Clock()
    TIMER_TICK = 1/cycles_per_frame  # 60Hz
    last_timer_update = time.time()
    quit_game = False

    while not quit_game:
        quit_game = platform.process_input(chip8.keypad)
        for _ in range(cycles_per_frame):
            chip8.cycle()
        # Timers at 60Hz
        current_time = time.time()
        if current_time - last_timer_update >= TIMER_TICK:
            chip8.update_timers()
            last_timer_update += TIMER_TICK
        platform.update(chip8.video)
        clock.tick((cycles_per_frame*3.75))  # Cap at 60 FPS

    pygame.quit()

if __name__ == "__main__":
    main()