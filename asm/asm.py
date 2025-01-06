from binascii import unhexlify
from enum import auto, Enum
import re

from util import bin_obj, label, opcode, registers

VERSION = (0, 0, 0)

_REGISTER_MAP = {k: v for style in registers.REGISTER_NAMES.values() for v, k in enumerate(style)}

_RE_OP = "[\\w\\d]+"
_RE_REG = "[\\w\\d]+"
_RE_IMM = "[-\\+]?\\d+"
_RE_LABEL = "[\\$\\w\\d]+"
_RE_ALPHA = "[\\w\\d]+"
_RE_POSNUM = "\\d+"
_RE_HEXNUM = "[a-f\\d]+"
_RE_DEF_LABEL = re.compile(f"^({_RE_LABEL}):\\s*$", re.IGNORECASE)
_RE_DEF_GLOBAL_LABEL = re.compile(f"^\\.global\\s+({_RE_LABEL}):\\s*$", re.IGNORECASE)
_RE_DIR_SECTION = re.compile(f"^\\.section\\s+({_RE_ALPHA})\\s*$", re.IGNORECASE)
_RE_DIR_PADDING = re.compile(f"^\\.padding\\s+({_RE_POSNUM})\\s*$", re.IGNORECASE)
_RE_DIR_BYTES = re.compile(f"^\\.bytes\\s+({_RE_HEXNUM})\\s*$", re.IGNORECASE)
_RE_INST_REG_REG = re.compile(f"^({_RE_OP})\\s+({_RE_REG})\\s+({_RE_REG})\\s+({_RE_REG})\\s*$", re.IGNORECASE)
_RE_INST_REG_IMM = re.compile(f"^({_RE_OP})\\s+({_RE_REG})\\s+({_RE_REG})\\s+({_RE_IMM})\\s*$", re.IGNORECASE)
_RE_INST_MEMORY = re.compile(f"^({_RE_OP})\\s+({_RE_REG})\\s+({_RE_IMM})\\s*\\(\\s*({_RE_REG})\\s*\\)\\s*$", re.IGNORECASE)
_RE_INST_BRANCH = re.compile(f"^({_RE_OP})\\s+({_RE_REG})\\s+({_RE_REG})\\s+({_RE_IMM}|{_RE_LABEL})(?:\\s+(likely|unlikely))?\\s*$", re.IGNORECASE)
_RE_INST_REG_LABEL = re.compile(f"({_RE_OP})\\s+({_RE_REG})\\s+({_RE_IMM}|{_RE_LABEL})\\s*$", re.IGNORECASE)
_RE_INST_TWO_REG = re.compile(f"({_RE_OP})\\s+({_RE_REG})\\s+({_RE_REG})\\s*$", re.IGNORECASE)

class AssemblerMode(Enum):

	NONE = auto()
	CODE = auto()
	DATA = auto()

class Assembler:

	code_local_labels: dict[str, label.Label]
	code_global_labels: dict[str, label.Label]
	data_global_labels: dict[str, label.Label]
	relocation_table: list[label.Relocation]
	code_current_offset: int
	data_current_offset: int
	instructions: list[int]
	data_section: bytearray

	def __init__(self):
		self.code_local_labels = {}
		self.code_global_labels = {}
		self.data_global_labels = {}
		self.relocation_table = []
		self.code_current_offset = 0
		self.data_current_offset = 0
		self.instructions = []
		self.data_section = bytearray()
	
	def assemble_file(self, input_file: str, output_file: str):
		lines = None
		self.instructions = []
		self.data_section = bytearray()
		self.code_current_offset = 0
		self.data_current_offset = 0
		with open(input_file, "r") as in_file:
			lines = in_file.readlines()
		mode = AssemblerMode.NONE
		for line in lines:
			line_data = line.split("//", 1)[0]
			if line_data.isspace():
				continue
			mode = self.assemble_line(line_data, mode)
		global_relocation_table = []
		for relocation in self.relocation_table:
			if relocation.symbol in self.code_local_labels:
				value = self.code_local_labels[relocation.symbol].offset
				if relocation.relative:
					value = value - relocation.offset
				mask = (1 << relocation.bit_len) - 1
				value >>= relocation.bit_shift
				value &= mask
				value <<= relocation.bit_offset
				mask = ~(mask << relocation.bit_offset)
				self.instructions[relocation.offset >> 2] = (self.instructions[relocation.offset >> 2] & mask) | value
			else:
				global_relocation_table.append(relocation)
		with open(output_file, "wb") as out_file:
			code_global_labels_section = bin_obj.generate_labels_section(self.code_global_labels)
			data_global_labels_section = bin_obj.generate_labels_section(self.data_global_labels)
			relocation_section = bin_obj.generate_relocation_section(global_relocation_table)
			code_section = bin_obj.generate_code_section(self.instructions)
			data_section = self.data_section

			code_global_labels_start = bin_obj.OBJ_HEADER_LENGTH
			data_global_labels_start = code_global_labels_start + len(code_global_labels_section)
			relocation_table_start = data_global_labels_start + len(data_global_labels_section)
			data_start = relocation_table_start + len(relocation_section)
			instructions_start = data_start + len(data_section)

			header = bin_obj.generate_obj_header(VERSION, code_global_labels_start, data_global_labels_start, relocation_table_start, data_start, len(data_section), instructions_start, len(self.instructions))

			out_file.write(header)
			out_file.write(code_global_labels_section)
			out_file.write(data_global_labels_section)
			out_file.write(relocation_section)
			out_file.write(data_section)
			out_file.write(code_section)
	
	def assemble_line(self, line: str, mode: AssemblerMode) -> AssemblerMode:
		# Section directives
		res = _RE_DIR_SECTION.match(line)
		if res != None:
			name = res.group(1).lower()
			if name == "code":
				return AssemblerMode.CODE
			if name == "data":
				return AssemblerMode.DATA
			raise RuntimeError(f"Unrecognized assembler section {name}")
		# Mode-specific behavior
		if mode == AssemblerMode.CODE:
			self.assemble_code_line(line)
		elif mode == AssemblerMode.DATA:
			self.assemble_data_line(line)
		return mode
	
	def assemble_code_line(self, line: str):
		# Local labels
		res = _RE_DEF_LABEL.match(line)
		if res != None:
			name = res.group(1)
			self.code_local_labels[name] = label.Label(name, label.LabelScope.LOCAL, self.code_current_offset)
			return
		# Global labels
		res = _RE_DEF_GLOBAL_LABEL.match(line)
		if res != None:
			name = res.group(1)
			self.code_global_labels[name] = label.Label(name, label.LabelScope.GLOBAL, self.code_current_offset)
			return
		# Instructions
		inst = self.assemble_instruction(line, self.code_current_offset)
		self.instructions.append(inst)
		self.code_current_offset += 4
	
	def assemble_data_line(self, line: str):
		# Local labels
		res = _RE_DEF_LABEL.match(line)
		if res != None:
			name = res.group(1)
			self.data_global_labels[name] = label.Label(name, label.LabelScope.LOCAL, self.data_current_offset)
			return
		# Global labels
		res = _RE_DEF_GLOBAL_LABEL.match(line)
		if res != None:
			name = res.group(1)
			self.data_global_labels[name] = label.Label(name, label.LabelScope.GLOBAL, self.data_current_offset)
			return
		res = _RE_DIR_PADDING.match(line)
		if res != None:
			count = int(res.group(1))
			self.data_section.extend(bytes(count))
			self.data_current_offset += count
			return
		res = _RE_DIR_BYTES.match(line)
		if res != None:
			hex_data = res.group(1)
			bytes_data = unhexlify(hex_data.encode())
			self.data_section.extend(bytes_data)
			self.data_current_offset += len(bytes_data)
			return
	
	def assemble_instruction(self, inst: str, offset: int) -> int:
		op = inst.split()[0]
		if op in ["add", "sub", "and", "or", "xor", "sll", "srl", "sra", "rl", "rr", "seq", "slt", "sltu"]:
			return self.assemble_rr_arithmetic(inst, offset)
		if op in ["addi", "andi", "ori", "xori", "seqi", "slti", "sltui"]:
			return self.assemble_ri_arithmetic(inst, offset)
		if op in ["slli", "srli", "srai", "rli", "rri"]:
			return self.assemble_ri_shift(inst, offset)
		if op in ["lw", "lh", "lhu", "lb", "lbu"]:
			return self.assemble_memory_load(inst, offset)
		if op in ["sw", "sh", "sb"]:
			return self.assemble_memory_store(inst, offset)
		if op in ["blt", "ble", "beq", "bne", "bgt", "bge", "bltu", "bleu", "bgtu", "bgeu"]:
			return self.assemble_conditional_branch(inst, offset)
		if op in ["ja", "jr"]:
			return self.assemble_jump(inst, offset)
		if op in ["jra", "jrr"]:
			return self.assemble_jump_register(inst, offset)
		if op in ["li"]:
			return self.assemble_load_immediate(inst, offset)
		if op in ["mv"]:
			return self.assemble_move(inst, offset)
		raise RuntimeError(f"Unrecognized instruction {op}")

	def evaluate_or_defer_int(self, string: str, offset: int, bit_offset: int, bit_len: int, bit_shift: int, relative: bool) -> int:
		res = 0
		try:
			res = int(string)
		except ValueError:
			self.relocation_table.append(label.Relocation(string, offset, bit_offset, bit_len, bit_shift, relative))
		return res
	
	def parse_reg(self, reg: str) -> int:
		if reg in _REGISTER_MAP:
			return _REGISTER_MAP[reg]
		raise RuntimeError(f"Unrecognized register {reg}")
	
	def parse_inst_reg_reg(self, inst: str, offset: int) -> tuple[str, int, int, int]:
		res = _RE_INST_REG_REG.match(inst)
		if res == None:
			raise RuntimeError(f"Could not parse instruction {inst}")
		return (res.group(1), self.parse_reg(res.group(2)), self.parse_reg(res.group(3)), self.parse_reg(res.group(4)))

	def parse_inst_reg_imm(self, inst: str, offset: int) -> tuple[str, int, int, int]:
		res = _RE_INST_REG_IMM.match(inst)
		if res == None:
			raise RuntimeError(f"Could not parse instruction {inst}")
		return (res.group(1), self.parse_reg(res.group(2)), self.parse_reg(res.group(3)), int(res.group(4)))

	def parse_inst_memory(self, inst: str, offset: int) -> tuple[str, int, int, int]:
		res = _RE_INST_MEMORY.match(inst)
		if res == None:
			raise RuntimeError(f"Could not parse instruction {inst}")
		# TODO: Better immediate parsing (label support?)
		return (res.group(1), self.parse_reg(res.group(2)), int(res.group(3)), self.parse_reg(res.group(4)))

	def parse_inst_branch(self, inst: str, offset: int, imm_bit_offset: int, imm_bit_len: int, imm_bit_shift: int, imm_relative: bool) -> tuple[str, int, int, int, str | None]:
		res = _RE_INST_BRANCH.match(inst)
		if res == None:
			raise RuntimeError(f"Could not parse instruction {inst}")
		dst = self.evaluate_or_defer_int(res.group(4), offset, imm_bit_offset, imm_bit_len, imm_bit_shift, imm_relative)
		return (res.group(1), self.parse_reg(res.group(2)), self.parse_reg(res.group(3)), dst, res.group(5))
	
	def parse_inst_reg_label(self, inst: str, offset: int, imm_bit_offset: int, imm_bit_len: int, imm_bit_shift: int, imm_relative: bool) -> tuple[str, int, int]:
		res = _RE_INST_REG_LABEL.match(inst)
		if res == None:
			raise RuntimeError(f"Could not parse instruction {inst}")
		dst = self.evaluate_or_defer_int(res.group(3), offset, imm_bit_offset, imm_bit_len, imm_bit_shift, imm_relative)
		return (res.group(1), self.parse_reg(res.group(2)), dst)

	def parse_inst_two_reg(self, inst: str, offset: int) -> tuple[str, int, int]:
		res = _RE_INST_TWO_REG.match(inst)
		if res == None:
			raise RuntimeError(f"Could not parse instruction {inst}")
		return (res.group(1), self.parse_reg(res.group(2)), self.parse_reg(res.group(3)))

	def assemble_rr_arithmetic(self, inst: str, offset: int) -> int:
		op, rd, rs1, rs2 = self.parse_inst_reg_reg(inst, offset)
		arith_op_lower, arith_op_upper = opcode.ARITH_OP_MAP[op]
		return opcode.Opcode.RR_ARITHMETIC \
			| (rd << 7) \
			| (rs1 << 12) \
			| (rs2 << 17) \
			| (arith_op_upper << 26) \
			| (arith_op_lower << 29)
	
	def assemble_ri_arithmetic(self, inst: str, offset: int) -> int:
		op, rd, rs1, imm = self.parse_inst_reg_imm(inst, offset)
		arith_op_lower, _ = opcode.ARITH_OP_MAP[op]
		return opcode.Opcode.RI_ARITHMETIC \
			| (rd << 7) \
			| (rs1 << 12) \
			| ((imm & 0xFFF) << 17) \
			| (arith_op_lower << 29)
	
	def assemble_ri_shift(self, inst: str, offset: int) -> int:
		op, rd, rs1, imm = self.parse_inst_reg_imm(inst, offset)
		arith_op_lower, arith_op_upper = opcode.ARITH_OP_MAP[op]
		return opcode.Opcode.RI_ARITHMETIC \
			| (rd << 7) \
			| (rs1 << 12) \
			| ((imm & 0x1F) << 17) \
			| (arith_op_upper << 26) \
			| (arith_op_lower << 29)

	def assemble_memory_load(self, inst: str, offset: int) -> int:
		op, rd, imm, rs2 = self.parse_inst_memory(inst, offset)
		memop = opcode.MEM_LOAD_OP_MAP[op]
		return opcode.Opcode.MEM_LOAD \
			| (rd << 7) \
			| ((imm & 0x1F) << 12) \
			| (rs2 << 17) \
			| (((imm >> 5) & 0x7F) << 22) \
			| (memop << 29)
	
	def assemble_memory_store(self, inst: str, offset: int) -> int:
		op, rs1, imm, rs2 = self.parse_inst_memory(inst, offset)
		memop = opcode.MEM_STORE_OP_MAP[op]
		return opcode.Opcode.MEM_STORE \
			| ((imm & 0x1F) << 7) \
			| (rs1 << 12) \
			| (rs2 << 17) \
			| (((imm >> 5) & 0x7F) << 22) \
			| (memop << 29)

	def assemble_conditional_branch(self, inst: str, offset: int) -> int:
		op, rs1, rs2, dst, likely = self.parse_inst_branch(inst, offset, 22, 9, 2, True)
		cond = opcode.BRANCH_COND_MAP[op]
		return opcode.Opcode.COND_BRANCH \
			| ((0 if likely == None else 1) << 7) \
			| (cond << 8) \
			| (rs1 << 12) \
			| (rs2 << 17) \
			| (((dst // 4) & 0x1FF) << 22) \
			| ((1 if likely == "likely" else 0) << 31)
	
	def assemble_jump(self, inst: str, offset: int) -> int:
		op, rd, dst = self.parse_inst_reg_label(inst, offset, 13, 19, 2, inst[1] == "r")
		relative = 0x1 if op == "jr" else 0x0
		return opcode.Opcode.JUMP \
			| (rd << 7) \
			| (relative << 12) \
			| (((dst // 4) & 0x7FFFF) << 13)

	def assemble_jump_register(self, inst: str, offset: int) -> int:
		op, rd, rs2 = self.parse_inst_two_reg(inst, offset)
		relative = 0x1 if op == "jrr" else 0x0
		return opcode.Opcode.JUMP_REG \
			| (rd << 7) \
			| (relative << 12) \
			| (rs2 << 17)
	
	def assemble_load_immediate(self, inst: str, offset: int) -> int:
		# TODO: Support big immediates
		op, rd, dst = self.parse_inst_reg_label(inst, offset, 17, 12, 0, False)
		arith_op_lower, arith_op_upper = opcode.ARITH_OP_MAP["add"]
		return opcode.Opcode.RI_ARITHMETIC \
			| (rd << 7) \
			| ((dst & 0xFFF) << 17) \
			| (arith_op_upper << 26) \
			| (arith_op_lower << 29)
	
	def assemble_move(self, inst: str, offset: int) -> int:
		op, rd, rs1 = self.parse_inst_two_reg(inst, offset)
		arith_op_lower, arith_op_upper = opcode.ARITH_OP_MAP["add"]
		return opcode.Opcode.RR_ARITHMETIC \
			| (rd << 7) \
			| (rs1 << 12) \
			| (arith_op_upper << 26) \
			| (arith_op_lower << 29)