from util import bits, opcode, registers

class Disassembler:

	reg_style: str

	def __init__(self):
		self.reg_style = "xnum"

	def disassemble_instruction(self, instruction: int) -> str:
		if instruction == 0:
			return "nop"
		try:
			opcode = instruction & 0x7F
			if opcode not in _OPCODE_MAP:
				return "....."
			return _OPCODE_MAP[opcode](self, instruction)
		except:
			return "....."

	def get_rd(self, instruction: int):
		return registers.REGISTER_NAMES[self.reg_style][(instruction >> 7) & 0x1F]

	def get_rs1(self, instruction: int):
		return registers.REGISTER_NAMES[self.reg_style][(instruction >> 12) & 0x1F]
	
	def get_rs2(self, instruction: int):
		return registers.REGISTER_NAMES[self.reg_style][(instruction >> 17) & 0x1F]
	
	def disassemble_rr_arithmetic(self, instruction: int) -> str:
		opcode_lower = (instruction >> 29) & 0x7
		opcode_upper = (instruction >> 26) & 0x7
		op = _RR_ARITH_OP_MAP[opcode_upper](opcode_lower)
		return f"{op} {self.get_rd(instruction)} {self.get_rs1(instruction)} {self.get_rs2(instruction)}"

	def disassemble_ri_arithmetic(self, instruction: int) -> str:
		opcode_lower = (instruction >> 29) & 0x7
		opcode_upper = (instruction >> 26) & 0x7
		op = _RI_ARITH_OP_MAP[opcode_lower](opcode_upper)
		imm = 0
		if opcode_upper == opcode.ArithOp.SLL:
			imm = (instruction >> 17) & 0x1F
		else:
			imm = bits.twos_complement_to_python((instruction >> 17) & 0xFFF, 12)
		return f"{op} {self.get_rd(instruction)} {self.get_rs1(instruction)} {imm}"

	def disassemble_memory_load(self, instruction: int) -> str:
		memop = (instruction >> 29) & 0x7
		op = _MEM_LOAD_OP_MAP[memop]
		imm_bits = ((instruction >> 12) & 0x1F) | (((instruction >> 22) & 0x7F) << 5)
		imm = bits.twos_complement_to_python(imm_bits, 12)
		return f"{op} {self.get_rd(instruction)} {imm}({self.get_rs2(instruction)})"
	
	def disassemble_memory_store(self, instruction: int) -> str:
		memop = (instruction >> 29) & 0x7
		op = _MEM_STORE_OP_MAP[memop]
		imm_bits = ((instruction >> 7) & 0x1F) | (((instruction >> 22) & 0x7F) << 5)
		imm = bits.twos_complement_to_python(imm_bits, 12)
		return f"{op} {self.get_rs1(instruction)} {imm}({self.get_rs2(instruction)})"

	def disassemble_conditional_branch(self, instruction: int) -> str:
		cond = (instruction >> 8) & 0x7
		signed = (instruction >> 11) & 0b1
		op = _BRANCH_COND_MAP[cond](signed)
		imm = bits.twos_complement_to_python((instruction >> 22) & 0x1FF, 9) * 4
		likely = ""
		if (instruction >> 7) & 0b1:
			likely = " likely" if (instruction >> 31) & 0b1 else " unlikely"
		return f"{op} {self.get_rs1(instruction)} {self.get_rs2(instruction)} {imm}{likely}"
	
	def disassemble_jump(self, instruction: int) -> str:
		relative = (instruction >> 12) & 0b1
		op = "jr" if relative else "ja"
		imm = bits.twos_complement_to_python((instruction >> 13) & 0x7FFFF, 19) * 4
		return f"{op} {self.get_rd(instruction)} {imm}"
	
	def disassemble_jump_register(self, instruction: int) -> str:
		relative = (instruction >> 12) & 0b1
		op = "jrr" if relative else "jra"
		return f"{op} {self.get_rd(instruction)} {self.get_rs2(instruction)}"

_OPCODE_MAP = {
	opcode.Opcode.RR_ARITHMETIC: Disassembler.disassemble_rr_arithmetic,
	opcode.Opcode.RI_ARITHMETIC: Disassembler.disassemble_ri_arithmetic,
	opcode.Opcode.MEM_LOAD: Disassembler.disassemble_memory_load,
	opcode.Opcode.MEM_STORE: Disassembler.disassemble_memory_store,
	opcode.Opcode.COND_BRANCH: Disassembler.disassemble_conditional_branch,
	opcode.Opcode.JUMP: Disassembler.disassemble_jump,
	opcode.Opcode.JUMP_REG: Disassembler.disassemble_jump_register,
}

_RR_ARITH_OP_MAP = {
	opcode.ArithOp.ADD: lambda l: "sub" if l & 0b001 else "add",
	opcode.ArithOp.AND: lambda l: "and",
	opcode.ArithOp.OR: lambda l: "or",
	opcode.ArithOp.XOR: lambda l: "xor",
	opcode.ArithOp.SLL: lambda l: ("rr" if l & 0b001 else "rl") if l & 0b100 else (("sra" if l & 0b010 else "srl") if l & 0b001 else "sll"),
	opcode.ArithOp.SEQ: lambda l: "seq",
	opcode.ArithOp.SLT: lambda l: "slt",
	opcode.ArithOp.SLTU: lambda l: "sltu",
}

_RI_ARITH_OP_MAP = {
	opcode.ArithOp.ADD: lambda l: "addi",
	opcode.ArithOp.AND: lambda l: "andi",
	opcode.ArithOp.OR: lambda l: "ori",
	opcode.ArithOp.XOR: lambda l: "xori",
	opcode.ArithOp.SLL: lambda l: ("rri" if l & 0b001 else "rli") if l & 0b100 else (("srai" if l & 0b010 else "srli") if l & 0b001 else "slli"),
	opcode.ArithOp.SEQ: lambda l: "seqi",
	opcode.ArithOp.SLT: lambda l: "slti",
	opcode.ArithOp.SLTU: lambda l: "sltui",
}

_BRANCH_COND_MAP = {
	0b001: lambda l: "bltu" if l else "blt",
	0b011: lambda l: "bleu" if l else "ble",
	0b010: lambda l: "beq",
	0b101: lambda l: "bne",
	0b100: lambda l: "bgtu" if l else "bgt",
	0b110: lambda l: "bgeu" if l else "bge",
}

_MEM_LOAD_OP_MAP = {
	0b111: "lw",
	0b101: "lh",
	0b001: "lhu",
	0b100: "lb",
	0b000: "lbu",
}

_MEM_STORE_OP_MAP = {
	0b111: "sw",
	0b101: "sh",
	0b100: "sb",
}