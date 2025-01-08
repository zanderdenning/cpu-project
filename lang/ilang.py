from enum import auto, Enum
from io import TextIOWrapper
from typing import Any

from lang import types

class ValueType(Enum):

	NONE = auto()
	REG = auto()
	IMM = auto()
	LABEL = auto()
	CONST_REG = auto()

class InstructionType(Enum):
	
	COPY = auto()
	LOAD = auto()
	STORE = auto()
	CALL = auto()
	RET = auto()
	INLINE_ASM = auto()
	SYSCALL = auto()
	BINARY_OP = auto()

class Instruction:

	instruction_type: InstructionType
	rd: int | str | None
	rs1: int | str | None
	rs2: int | str | None
	rs1_type: ValueType
	rs2_type: ValueType
	data: Any
	do_not_optimize: bool

	def __init__(self, instruction_type: InstructionType, rd: int | str | None, rs1: int | str | None, rs2: int | str | None, rs1_type: ValueType, rs2_type: ValueType, do_not_optimize: bool, data: Any):
		self.instruction_type = instruction_type
		self.rd = rd
		self.rs1 = rs1
		self.rs2 = rs2
		self.rs1_type = rs1_type
		self.rs2_type = rs2_type
		self.data = data
		self.do_not_optimize = do_not_optimize
	
	def __str__(self):
		return f"{self.instruction_type.name}  {self.rd}  {self.rs1}/{self.rs1_type.name} {self.rs2}/{self.rs1_type.name}  [{self.data}]  {self.do_not_optimize}"

REG_NONE = 0
REG_FP = "fp"
REG_RET = "a0"
REG_TMP_A = "t14"
REG_TMP_B = "t15"

class InstructionList:

	instructions: list[Instruction]
	_current_register: int
	basic_blocks: list[tuple[int, int]]
	edges: list[list[int]]
	live_vars_in: list[set[int]]
	live_vars_out: list[set[int]]
	register_map: list[int]
	temporaries: dict[int, int]
	temporaries_count: int
	function_type: types.FunctionType | None

	def __init__(self, function_type: types.FunctionType | None):
		self.instructions = []
		self._current_register = 0
		self.basic_blocks = []
		self.edges = []
		self.live_vars_in = []
		self.live_vars_out = []
		self.register_map = []
		self.temporaries = []
		self.temporaries_count = 0
		self.function_type = function_type
	
	def get_register(self) -> int:
		self._current_register += 1
		return self._current_register

	def _reg(self, reg: int) -> str:
		return f"x{self.register_map[reg]}"

	def _mem_access(self, size: int, signed: bool) -> str:
		if size == 1:
			return "b" if signed else "bu"
		if size == 2:
			return "h" if signed else "hu"
		return "w"

	def put_in_reg(self, value: int | str | None, value_type: ValueType, file_out: TextIOWrapper, tmp_var: str) -> str:
		# TODO: Support big immediates
		if value_type == ValueType.IMM or value_type == ValueType.LABEL:
			file_out.write(f"li {tmp_var} {value}\n")
		elif value_type == ValueType.REG:
			return self._reg(value)
		elif value_type == ValueType.CONST_REG:
			return value
		return tmp_var

	# Copies
	
	def write_constant_int(self, rd: int, value: int):
		self.instructions.append(Instruction(InstructionType.COPY, rd, value, None, ValueType.IMM, ValueType.NONE, False, None))
	
	def write_global_addr_load(self, rd: int, value: str):
		self.instructions.append(Instruction(InstructionType.COPY, rd, value, None, ValueType.LABEL, ValueType.NONE, False, None))
	
	def output_copy(self, inst: Instruction, file_out: TextIOWrapper):
		# TODO: Support big immediates
		if inst.rs1_type == ValueType.REG:
			file_out.write(f"mv {self._reg(inst.rd)} {self._reg(inst.rs1)}\n")
		elif inst.rs1_type == ValueType.CONST_REG:
			file_out.write(f"mv {self._reg(inst.rd)} {inst.rs1}\n")
		elif inst.rs1_type == ValueType.IMM or inst.rs1_type == ValueType.LABEL:
			file_out.write(f"li {self._reg(inst.rd)} {inst.rs1}\n")

	# Stores

	def write_arg_store(self, value: int, offset: int, locals_size: int):
		self.instructions.append(Instruction(InstructionType.STORE, REG_NONE, REG_FP, value, ValueType.CONST_REG, ValueType.REG, True, (-4 - offset - locals_size, True, 4, False)))

	def write_local_store(self, value: int, offset: int, size: int):
		self.instructions.append(Instruction(InstructionType.STORE, REG_NONE, REG_FP, value, ValueType.CONST_REG, ValueType.REG, True, (-4 - offset, False, size, False)))
	
	def write_nested_local_store(self, value: int, fp: int, offset: int, size: int):
		self.instructions.append(Instruction(InstructionType.STORE, REG_NONE, fp, value, ValueType.REG, ValueType.REG, True, (-4 - offset, False, size, False)))
	
	def write_global_store(self, value: int, symbol: str, size: int):
		self.instructions.append(Instruction(InstructionType.STORE, REG_NONE, symbol, value, ValueType.LABEL, ValueType.REG, True, (0, False, size, False)))
	
	def output_store(self, inst: Instruction, file_out: TextIOWrapper):
		rs1 = self.put_in_reg(inst.rs1, inst.rs1_type, file_out, REG_TMP_A)
		rs2 = self.put_in_reg(inst.rs2, inst.rs2_type, file_out, REG_TMP_B)
		offset = inst.data[0]
		if inst.data[1]:
			offset -= self.temporaries_count * 4
		file_out.write(f"s{self._mem_access(inst.data[2], inst.data[3])} {rs2} {offset}({rs1})\n")
	
	# Loads

	def write_local_load(self, rd: int, offset: int, size: int, signed: bool):
		self.instructions.append(Instruction(InstructionType.LOAD, rd, REG_FP, None, ValueType.CONST_REG, ValueType.NONE, False, (-4 - offset, False, size, signed)))
	
	def write_nested_local_load(self, rd: int, fp: int, offset: int, size: int, signed: bool):
		self.instructions.append(Instruction(InstructionType.LOAD, rd, fp, None, ValueType.REG, ValueType.NONE, False, (-4 - offset, False, size, signed)))
	
	def write_global_load(self, rd: int, symbol: str, size: int, signed: bool):
		self.instructions.append(Instruction(InstructionType.LOAD, rd, symbol, None, ValueType.LABEL, ValueType.NONE, False, (0, False, size, signed)))

	def output_load(self, inst: Instruction, file_out: TextIOWrapper):
		rs1 = self.put_in_reg(inst.rs1, inst.rs1_type, file_out, REG_TMP_A)
		offset = inst.data[0]
		if inst.data[1]:
			offset -= self.temporaries_count * 4
		file_out.write(f"l{self._mem_access(inst.data[2], inst.data[3])} {self._reg(inst.rd)} {offset}({rs1})\n")

	# Calls

	def write_call(self, rd: int, func_addr: int, locals_size: int, args_size: int):
		self.instructions.append(Instruction(InstructionType.CALL, rd, func_addr, None, ValueType.REG, ValueType.NONE, True, locals_size + args_size))
	
	def write_call_static(self, rd: int, func_name: str, locals_size: int, args_size: int):
		self.instructions.append(Instruction(InstructionType.CALL, rd, func_name, None, ValueType.LABEL, ValueType.NONE, True, locals_size + args_size))
	
	def output_call(self, inst: Instruction, file_out: TextIOWrapper):
		saved_fp_offset = 4 + inst.data + self.temporaries_count * 4
		static_link_offset = saved_fp_offset + 4
		new_fp_offset = static_link_offset + 4
		file_out.write(f"sw fp -{saved_fp_offset}(fp)\n")
		file_out.write(f"sw fp -{static_link_offset}(fp)\n") # TODO: Correct static link
		file_out.write(f"addi fp fp -{new_fp_offset}\n")
		# TODO: Support big immediates
		if inst.rs1_type == ValueType.REG:
			file_out.write(f"jra ra {self._reg(inst.rs1)}\n")
		elif inst.rs1_type == ValueType.CONST_REG:
			file_out.write(f"jra ra {inst.rs1}\n")
		elif inst.rs1_type == ValueType.IMM or inst.rs1_type == ValueType.LABEL:
			file_out.write(f"ja ra {inst.rs1}\n")
		file_out.write(f"mv {self._reg(inst.rd)} a0\n")
	
	# Returns
	
	def write_ret(self, value: int):
		self.instructions.append(Instruction(InstructionType.RET, REG_NONE, value, None, ValueType.REG, ValueType.NONE, True, None))
	
	def write_ret_void(self):
		self.instructions.append(Instruction(InstructionType.RET, REG_NONE, None, None, ValueType.NONE, ValueType.NONE, True, None))
	
	def output_ret(self, inst: Instruction, file_out: TextIOWrapper):
		if inst.rs1_type != ValueType.NONE:
			rs1 = self.put_in_reg(inst.rs1, inst.rs1_type, file_out, REG_TMP_A)
			file_out.write(f"mv a0 {rs1}\n")
		file_out.write(f"lw ra 0(fp)\n")
		file_out.write(f"lw fp 8(fp)\n")
		file_out.write(f"jra zero ra\n")
	
	# Inline ASM
	
	def write_inline_asm(self, asm: str):
		self.instructions.append(Instruction(InstructionType.INLINE_ASM, REG_NONE, None, None, ValueType.NONE, ValueType.NONE, True, asm))
	
	def output_inline_asm(self, inst: Instruction, file_out: TextIOWrapper):
		file_out.write(f"{inst.data}\n")
	
	# Syscalls

	def write_syscall(self, syscall: int):
		self.instructions.append(Instruction(InstructionType.SYSCALL, REG_NONE, None, None, ValueType.NONE, ValueType.NONE, True, syscall))
	
	def output_syscall(self, inst: Instruction, file_out: TextIOWrapper):
		file_out.write(f"syscall {inst.data}\n")
	
	# Binary operations
	
	def write_binary_op(self, rd: int, rs1: int, rs2: int, op: str):
		self.instructions.append(Instruction(InstructionType.BINARY_OP, rd, rs1, rs2, ValueType.REG, ValueType.REG, False, op))
	
	def output_binary_op(self, inst: Instruction, file_out: TextIOWrapper):
		# TODO: Use RI instructions
		rs1 = self.put_in_reg(inst.rs1, inst.rs1_type, file_out, REG_TMP_A)
		rs2 = self.put_in_reg(inst.rs2, inst.rs2_type, file_out, REG_TMP_B)
		file_out.write(f"{inst.data} {self._reg(inst.rd)} {rs1} {rs2}\n")

	# TODO: Below this line

	def write_load_fp(self, rd: int):
		self.instructions.append(Instruction(InstructionType.LOAD_FP, rd, REG_NONE, REG_NONE, 0, False))
	
	def write_nested_load_fp(self, rd: int, fp: int):
		self.instructions.append(Instruction(InstructionType.NESTED_LOAD_FP, rd, fp, REG_NONE, 0, False))
	
	def write_load_static_link(self, rd: int):
		self.instructions.append(Instruction(InstructionType.LOAD_STATIC_LINK, rd, REG_NONE, REG_NONE, 0, False))
	
	def write_nested_load_static_link(self, rd: int, fp: int):
		self.instructions.append(Instruction(InstructionType.NESTED_LOAD_STATIC_LINK, rd, fp, REG_NONE, 0, False))

	# Optimization and generation

	def generate_code(self, out_file: TextIOWrapper):
		print()
		self.split_basic_blocks()
		self.live_vars_in = [set() for _ in self.basic_blocks]
		self.live_vars_out = [set() for _ in self.basic_blocks]
		while self.liveness_analysis():
			pass # Continue until constant
		print(self.live_vars_in)
		print(self.live_vars_out)
		self.register_map = [0 for _ in range(self._current_register + 1)]
		self.allocate_registers()
		print(self.register_map)
		for inst in self.instructions:
			_INSTRUCTION_WRITE_MAP[inst.instruction_type](self, inst, out_file)

	def split_basic_blocks(self):
		# TODO: Actually split this by branches
		self.basic_blocks = [(0, len(self.instructions) // 2), (len(self.instructions) // 2, len(self.instructions))]
		self.edges = [[False for _ in self.basic_blocks] for _ in self.basic_blocks]
		self.edges[0][1] = True
	
	def liveness_analysis(self) -> bool:
		changed = False

		for i in range(len(self.basic_blocks)):
			block = self.basic_blocks[i]

			current_vars_out_count = len(self.live_vars_out[i])
			for j in self.edges[i]:
				if j:
					self.live_vars_out[i].update(self.live_vars_in[j])
			if current_vars_out_count != len(self.live_vars_out[i]):
				changed = True
			
			new_live_vars_in = set(self.live_vars_out[i])
			for j in range(block[1] - 1, block[0] - 1, -1):
				inst = self.instructions[j]
				if inst.rd != REG_NONE:
					new_live_vars_in.discard(inst.rd)
				if inst.rs1_type == ValueType.REG:
					print((inst.rs1, inst.rs1_type))
					new_live_vars_in.add(inst.rs1)
				if inst.rs2_type == ValueType.REG:
					print((inst.rs2, inst.rs2_type))
					new_live_vars_in.add(inst.rs2)
			if new_live_vars_in != self.live_vars_in[i]:
				changed = True
			self.live_vars_in[i] = new_live_vars_in

		return changed

	def allocate_registers(self):
		rig = [set() for _ in range(self._current_register + 1)]

		for i in range(len(self.basic_blocks)):
			block = self.basic_blocks[i]

			live_vars = self.live_vars_out[i]
			for reg in live_vars:
				rig[reg].update(live_vars)
			for j in range(block[1] - 1, block[0] - 1, -1):
				inst = self.instructions[j]
				if inst.rd != REG_NONE:
					live_vars.discard(inst.rd)
				if inst.rs1_type == ValueType.REG:
					live_vars.add(inst.rs1)
				if inst.rs2_type == ValueType.REG:
					live_vars.add(inst.rs2)
				for reg in live_vars:
					rig[reg].update(live_vars)
		
		for i in range(len(rig)):
			rig[i].discard(i)
		
		print(rig)

		available_registers = set(i for i in range(9, 30))
		available_registers_count = len(available_registers)

		for i in range(1, self._current_register + 1):
			edges = rig[i]
			if len(edges) > available_registers_count - 1:
				self.register_map[i] = -1
				for j in edges:
					rig[j].discard(j)
				continue
			neighbors = set()
			for j in edges:
				neighbors.add(self.register_map[j])
			mapped_register = (available_registers - neighbors).pop()
			self.register_map[i] = mapped_register

_INSTRUCTION_WRITE_MAP = {
	InstructionType.COPY: InstructionList.output_copy,
	InstructionType.LOAD: InstructionList.output_load,
	InstructionType.STORE: InstructionList.output_store,
	InstructionType.CALL: InstructionList.output_call,
	InstructionType.RET: InstructionList.output_ret,
	InstructionType.INLINE_ASM: InstructionList.output_inline_asm,
	InstructionType.SYSCALL: InstructionList.output_syscall,
	InstructionType.BINARY_OP: InstructionList.output_binary_op,
}