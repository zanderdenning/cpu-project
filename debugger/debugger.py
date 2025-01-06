import curses
import curses.textpad
import typing

from asm import asm, disasm
from emu import emu
from util import registers

def command_quit(command: list[str], debugger: "Debugger") -> bool:
	return False

def command_init(command: list[str], debugger: "Debugger") -> bool:
	debugger.emulator.reset()
	return True

def command_execute(command: list[str], debugger: "Debugger") -> bool:
	inst = asm.Assembler().assemble_instruction(" ".join(command[1:]), 0)
	debugger.emulator.execute_instruction(inst, False)
	return True

def command_load(command: list[str], debugger: "Debugger") -> bool:
	path = command[1]
	debugger.emulator.load_exe(path)
	return True

def command_regstyle(command: list[str], debugger: "Debugger") -> bool:
	style = command[1]
	if style not in registers.REGISTER_NAMES:
		debugger.log(f"Unrecognized register style {style}")
		return True
	debugger.reg_style = style
	debugger.disassembler.reg_style = style
	return True

def command_step(command: list[str], debugger: "Debugger") -> bool:
	debugger.emulator.step()
	return True

_COMMAND_MAP = {
	"quit": command_quit,
	"q": command_quit,
	"exit": command_quit,
	"init": command_init,
	"i": command_init,
	"execute": command_execute,
	"x": command_execute,
	"load": command_load,
	"l": command_load,
	"regstyle": command_regstyle,
	"step": command_step,
	"s": command_step,
}

class Debugger:

	stdscr: curses.window
	registers_window: curses.window
	console_window: curses.window
	output_window: curses.window
	emulator: emu.Emulator
	console: curses.textpad.Textbox
	last_output: str
	disassembler: disasm.Disassembler
	reg_style: str

	def __init__(self, stdscr: curses.window):
		self.stdscr = stdscr
		self.stdscr.clear()
		self.console_window = curses.newwin(0, 0, 0, 0)
		self.registers_window = curses.newwin(0, 0, 0, 0)
		self.output_window = curses.newwin(0, 0, 0, 0)
		self.instruction_window = curses.newwin(0, 0, 0, 0)
		self.resize()
		self.console = curses.textpad.Textbox(self.console_window)
		self.emulator = emu.Emulator()
		self.last_output = ""
		self.disassembler = disasm.Disassembler()
		self.reg_style = "xnum"
		while True:
			self.update_console_window()
			self.update_registers_window()
			self.update_output_window()
			self.update_instruction_window()
			self.stdscr.refresh()
			self.console.edit()
			try:
				command = self.console.gather().split()
				if len(command) == 0:
					continue
				if command[0] not in _COMMAND_MAP:
					self.log(f"Unknown command {command[0]}")
					continue
				func = _COMMAND_MAP[command[0]]
				result = func(command, self)
				if not result:
					break
			except Exception as e:
				self.log(e.args[0])
				pass
	
	def resize(self):
		self.stdscr.clear()
		h, w = self.stdscr.getmaxyx()
		self.registers_window.resize(17, w // 2 - 2)
		self.registers_window.mvwin(1, 1)
		curses.textpad.rectangle(self.stdscr, 0, 0, 18, w // 2 - 1)
		self.console_window.resize(1, w // 2 - 2)
		self.console_window.mvwin(h - 2, 1)
		curses.textpad.rectangle(self.stdscr, h - 3, 0, h - 1, w // 2 - 1)
		self.output_window.resize(h - 19 - 3 - 2, w // 2 - 2)
		self.output_window.mvwin(20, 1)
		curses.textpad.rectangle(self.stdscr, 19, 0, h - 4, w // 2 - 1)
		self.instruction_window.resize(h - 2, w // 2 - 3)
		self.instruction_window.mvwin(1, w // 2 + 1)
		curses.textpad.rectangle(self.stdscr, 0, w // 2, h - 1, w - 2)
		self.stdscr.refresh()
	
	def log(self, msg: typing.Any):
		self.last_output = str(msg)

	def update_registers_window(self):
		self.registers_window.clear()
		reg_names = registers.REGISTER_NAMES[self.reg_style]
		reg_name_len = max(map(len, reg_names))
		self.registers_window.addstr(0, 0, "PC".ljust(reg_name_len))
		pc_value_str = "0x{:08X}".format(self.emulator.pc)
		self.registers_window.addstr(0, reg_name_len + 2, pc_value_str)
		for i in range(32):
			start_x = 0 if i < 16 else self.registers_window.getmaxyx()[1] // 2 + 1
			self.registers_window.addstr(i % 16 + 1, start_x, reg_names[i].ljust(reg_name_len))
			value_str = "0x{:08X}".format(self.emulator.registers[i])
			self.registers_window.addstr(i % 16 + 1, start_x + reg_name_len + 2, value_str)
		self.registers_window.refresh()
	
	def update_console_window(self):
		self.console_window.clear()
	
	def update_output_window(self):
		self.output_window.clear()
		self.output_window.addstr(0, 0, self.last_output)
		self.output_window.refresh()
	
	def update_instruction_window(self):
		self.instruction_window.clear()
		h, w = self.instruction_window.getmaxyx()
		start = self.emulator.pc // 4 - h // 2
		start = min(0x0FFFFFFF - h + 1, max(0, start))
		for i in range(h):
			addr = ((i + start) * 4) & 0xFFFFFFFF
			if addr == self.emulator.pc:
				self.instruction_window.addstr(i, 0, ">")
			self.instruction_window.addstr(i, 2, "{:08X}".format(addr))
			instruction = self.emulator.get_word(addr)
			self.instruction_window.addstr(i, 12, "{:08X}".format(instruction))
			self.instruction_window.addstr(i, 22, self.disassembler.disassemble_instruction(instruction))
		self.instruction_window.refresh()

def run_debugger():
	curses.wrapper(Debugger)
