import io

from util import bin_obj, bits, opcode

VALUE_MASK = 0xFFFFFFFF
BYTE_MASK = 0xFF
REG_MASK = 0x1F
REG_FP = 2

class Emulator:

	memory: dict[int, int]
	registers: list[int]
	pc: int

	def __init__(self):
		self.reset(0)
	
	def reset(self, pc_init: int):
		self.memory = {}
		self.registers = [0 for _ in range(32)]
		self.pc = pc_init
	
	def set_register(self, rd: int, value: int):
		if rd == 0:
			return
		self.registers[rd] = value & VALUE_MASK
	
	def set_byte(self, addr: int, value: int):
		self.memory[addr & VALUE_MASK] = value & BYTE_MASK
	
	def get_byte(self, addr: int) -> int:
		return self.memory.get(addr & VALUE_MASK, 0)
	
	def set_half_word(self, addr: int, value: int):
		self.set_byte(addr, value)
		self.set_byte(addr + 1, (value >> 8))

	def get_half_word(self, addr: int) -> int:
		return (self.get_byte(addr + 1) << 8) | self.get_byte(addr)

	def set_word(self, addr: int, value: int):
		self.set_half_word(addr, value)
		self.set_half_word(addr + 2, (value >> 16))

	def get_word(self, addr: int) -> int:
		return (self.get_half_word(addr + 2) << 16) | self.get_half_word(addr) 
	
	def set_pc(self, value: int):
		self.pc = value & VALUE_MASK
	
	def pc_inc(self):
		self.set_pc(self.pc + 4)
	
	def load_exe(self, path: str):
		with open(path, "rb") as file:
			version, instruction_start, instructions_count, data_start, data_length, main = bin_obj.parse_exe_header(file)
			self.reset(main)
			file.seek(0)
			self.load_memory(bin_obj.EXE_START_ADDR, list(file.read()))
			self.registers[REG_FP] = 0xFFFFFFE0
			
	def load_memory(self, addr: int, string: list[int], stride: int = 1):
		for i in string:
			self.set_byte(addr, i)
			addr += stride
	
	def step(self):
		self.execute_instruction(self.get_word(self.pc), True)
	
	def execute_instruction(self, instruction: int, update_pc: bool):
		opcode = instruction & 0x7F
		func = _OPCODE_MAP[opcode]
		func(self, instruction, update_pc)
	
	def get_rd(self, instruction: int):
		return (instruction >> 7) & REG_MASK
	
	def get_rs1(self, instruction: int):
		return (instruction >> 12) & REG_MASK
	
	def get_rs2(self, instruction: int):
		return (instruction >> 17) & REG_MASK
	
	def execute_arithmetic_instruction(self, instruction: int, update_pc: bool, reg_reg: bool):
		rd = self.get_rd(instruction)
		rs1 = self.get_rs1(instruction)
		rs2 = self.get_rs2(instruction)
		op_upper = (instruction >> 22) & 0b111
		op_lower = (instruction >> 29) & 0b111
		imm = bits.sign_extend((instruction >> 17) & 0xFFF, 12)
		a = self.registers[rs1]
		b = self.registers[rs2] if reg_reg else imm
		result = 0
		if op_lower == opcode.ArithOp.ADD:
			if reg_reg and (op_upper & 0b001):
				result = a - b
			else:
				result = a + b
		elif op_lower == opcode.ArithOp.AND:
			result = a & b
		elif op_lower == opcode.ArithOp.OR:
			result = a | b
		elif op_lower == opcode.ArithOp.XOR:
			result = a ^ b
		elif op_lower == opcode.ArithOp.SLL:
			if not reg_reg:
				b = (instruction >> 22) & 0x1F
			if (op_upper & 0b101) == 0b000:
				result = a << b
			elif (op_upper & 0b101) == 0b001:
				result = a >> b
				if op_upper & 0b010:
					if (a & 0x80000000) and result == 0:
						result = 0xFFFFFFFF
					else:
						result = bits.sign_extend(result, 32 - b)
			elif (op_upper & 0b101) == 0b100:
				result = (a << b) | (a >> (32 - b))
			elif (op_upper & 0b101) == 0b101:
				result = (a >> b) | (a << (32 - b))
		elif op_lower == opcode.ArithOp.SEQ:
			result = 1 if a == b else 0
		elif op_lower == opcode.ArithOp.SLT:
			result = 1 if bits.twos_complement_to_python(a, 32) < bits.twos_complement_to_python(b, 32) else 0
		elif op_lower == opcode.ArithOp.SLTU:
			result = 1 if a < b else 0
		self.set_register(rd, result)
		if update_pc:
			self.pc_inc()

	def execute_rr_arithmetic(self, instruction: int, update_pc: bool):
		self.execute_arithmetic_instruction(instruction, update_pc, True)
	
	def execute_ri_arithmetic(self, instruction: int, update_pc: bool):
		self.execute_arithmetic_instruction(instruction, update_pc, False)
	
	def execute_memory_load(self, instruction: int, update_pc: bool):
		rd = self.get_rd(instruction)
		rs2 = self.get_rs2(instruction)
		imm_bits = ((instruction >> 12) & 0x1F) | (((instruction >> 22) & 0x7F) << 5)
		imm = bits.twos_complement_to_python(imm_bits, 12)
		addr = (self.registers[rs2] + imm) & VALUE_MASK
		flag_half_word = (instruction >> 29) & 0b1
		flag_word = (instruction >> 30) & 0b1
		flag_signed = (instruction >> 31) & 0b1
		value = 0
		if flag_word:
			value = self.get_word(addr)
		elif flag_half_word:
			value = self.get_half_word(addr)
			if flag_signed and ((value >> 15) & 0b1):
				value |= 0xFFFF0000
		else:
			value = self.get_byte(addr)
			if flag_signed and ((value >> 7) & 0b1):
				value |= 0xFFFFFF00
		self.set_register(rd, value)
		if update_pc:
			self.pc_inc()
	
	def execute_memory_store(self, instruction: int, update_pc: bool):
		rs1 = self.get_rs1(instruction)
		rs2 = self.get_rs2(instruction)
		imm_bits = ((instruction >> 7) & 0x1F) | (((instruction >> 22) & 0x7F) << 5)
		imm = bits.twos_complement_to_python(imm_bits, 12)
		addr = (self.registers[rs2] + imm) & VALUE_MASK
		flag_half_word = (instruction >> 29) & 0b1
		flag_word = (instruction >> 30) & 0b1
		value = self.registers[rs1]
		if flag_word:
			self.set_word(addr, value)
		elif flag_half_word:
			self.set_half_word(addr, value)
		else:
			self.set_byte(addr, value)
		if update_pc:
			self.pc_inc()
	
	def execute_cond_branch(self, instruction: int, update_pc: bool):
		rs1 = self.get_rs1(instruction)
		rs2 = self.get_rs2(instruction)
		a = self.registers[rs1]
		b = self.registers[rs2]
		if not ((instruction >> 11) & 0b1):
			a = bits.twos_complement_to_python(a, 32)
			b = bits.twos_complement_to_python(b, 32)
		do_jump = False
		if ((instruction >> 8) & 0b1) and a < b:
			do_jump = True
		if ((instruction >> 9) & 0b1) and a == b:
			do_jump = True
		if ((instruction >> 10) & 0b1) and a > b:
			do_jump = True
		if do_jump:
			imm = bits.twos_complement_to_python((instruction >> 22) & 0x1FF, 9) * 4
			self.set_pc(self.pc + imm)
		elif update_pc:
			self.pc_inc()
	
	def execute_jump(self, instruction: int, update_pc: bool):
		relative = (instruction >> 12) & 0b1
		dst = bits.twos_complement_to_python((instruction >> 13) & 0x7FFFF, 19) * 4
		if relative:
			dst += self.pc
		self.set_register(self.get_rd(instruction), self.pc + 4)
		self.set_pc(dst)
	
	def execute_jump_register(self, instruction: int, update_pc: bool):
		relative = (instruction >> 12) & 0b1
		dst = self.registers[self.get_rs2(instruction)]
		if relative:
			dst += self.pc
		self.set_register(self.get_rd(instruction), self.pc + 4)
		self.set_pc(dst)

_OPCODE_MAP = {
	opcode.Opcode.RR_ARITHMETIC: Emulator.execute_rr_arithmetic,
	opcode.Opcode.RI_ARITHMETIC: Emulator.execute_ri_arithmetic,
	opcode.Opcode.MEM_LOAD: Emulator.execute_memory_load,
	opcode.Opcode.MEM_STORE: Emulator.execute_memory_store,
	opcode.Opcode.COND_BRANCH: Emulator.execute_cond_branch,
	opcode.Opcode.JUMP: Emulator.execute_jump,
	opcode.Opcode.JUMP_REG: Emulator.execute_jump_register,
}