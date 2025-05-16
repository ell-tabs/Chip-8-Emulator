from .constants import (
    START_ADDRESS,
    FONTSET_START_ADDRESS,
    FONTSET_SIZE,
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    fontset
)
import random
import time
import numpy as np

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
        else:
            pass

    def Table0(self):
        code = self.opcode & 0x00FF
        if code in self.table0:
            self.table0[code]()
        else:
            pass

    def TableE(self):
        code = self.opcode & 0x000F
        if code in self.tableE:
            self.tableE[code]()
        else:
            pass

    def TableF(self):
        code = self.opcode & 0x00FF
        if code in self.tableF:
            self.tableF[code]()
        else:
            pass

    def cycle(self):
        if self.pc >= len(self.memory) - 1:
            print(f"Program counter out of bounds: {self.pc}")
            return

        self.opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
        print(f"PC: {self.pc}, Opcode: 0x{self.opcode:04X}")

        try:
            prev_pc = self.pc
            self.table[(self.opcode & 0xF000) >> 12]()
            if self.pc == prev_pc:
                pass
        except Exception as e:
            print(f"Error executing opcode {hex(self.opcode)}: {e}")

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
            print(f"[00EE] Returning to address: {hex(self.pc)} | SP now: {self.sp}")
        else:
            print("[00EE] ERROR: Stack underflow — no return address to pop.")
            self.pc = START_ADDRESS

    def OP_1nnn(self):
        address = self.opcode & 0x0FFF
        self.pc = address

    def OP_2nnn(self):
        address = self.opcode & 0x0FFF
        print(f"[2NNN] At PC: {hex(self.pc)}, calling subroutine at: {hex(address)}")

        if self.sp < len(self.stack):
            self.stack[self.sp] = self.pc + 2
            self.sp += 1
            print(f"[2NNN] Stack push: return address {hex(self.pc + 2)} | SP now: {self.sp}")
            self.pc = address
        else:
            print("[2NNN] ERROR: Stack overflow — unable to push return address.")

    def OP_3xkk(self):
        Vx = (self.opcode & 0x0F00) >> 8
        byte = self.opcode & 0x00FF
        print(f"Checking if V{Vx} == {byte}: {self.registers[Vx]}")
        if self.registers[Vx] == byte:
            self.pc += 4  # skip next instruction
            print(f"Condition met, skipping next instruction. New PC: {self.pc}")
        else:
            self.pc += 2
            print(f"Condition not met, PC: {self.pc}")

    def OP_4xkk(self):
        Vx = (self.opcode & 0x0F00) >> 8
        byte = self.opcode & 0x00FF
        print(f"Checking if V{Vx} != {byte}: {self.registers[Vx]}")
        if self.registers[Vx] != byte:
            self.pc += 4  # skip next instruction
            print(f"Condition met, skipping next instruction. New PC: {self.pc}")
        else:
            self.pc += 2
            print(f"Condition not met, PC: {self.pc}")

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
        if self.registers[Vx] > self.registers[Vy]:
            self.registers[0xF] = 1
        else:
            self.registers[0xF] = 0
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
        if self.registers[Vy] > self.registers[Vx]:
            self.registers[0xF] = 1
        else:
            self.registers[0xF] = 0
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
        print(f"Setting index register I to: {hex(self.index)}")
        self.pc += 2

    def OP_Bnnn(self):
        address = self.opcode & 0x0FFF
        jump_address = self.registers[0] + address
        if jump_address < 0x200 or jump_address >= len(self.memory):
            print(f"Invalid jump address: {hex(jump_address)}")
        else:
            self.pc = jump_address

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
        print(f"Waiting for key press for V{Vx}...")
        for i in range(16):
            if self.keypad[i]:
                self.registers[Vx] = i
                print(f"Key {i} pressed, storing in V{Vx}")
                self.pc += 2
                return
        # If no key pressed, do not increment PC (wait)

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

        # Ones place
        self.memory[self.index + 2] = value % 10
        value //= 10

        # Tens place
        self.memory[self.index + 1] = value % 10
        value //= 10

        # Hundreds place
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