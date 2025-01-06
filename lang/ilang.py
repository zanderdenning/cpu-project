from enum import auto, Enum
from io import TextIOWrapper
from typing import Any

from lang import types

class InstructionType(Enum):
	
	CONST_INT = auto()
	GLOBAL_ADDR_LOAD = auto()
	ARG_STORE = auto()
	LOCAL_LOAD = auto()
	LOCAL_STORE = auto()
	NESTED_LOCAL_LOAD = auto()
	NESTED_LOCAL_STORE = auto()
	LOAD_FP = auto()
	NESTED_LOAD_FP = auto()
	LOAD_STATIC_LINK = auto()
	NESTED_LOAD_STATIC_LINK = auto()
	GLOBAL_LOAD = auto()
	GLOBAL_STORE = auto()
	CALL = auto()
	CALL_STATIC = auto()
	LOAD_STATIC_FUNC_ADDR = auto()
	RET = auto()
	RET_VOID = auto()
	INLINE_ASM = auto()
	SYSCALL = auto()
	BINARY_OP = auto()

class Instruction:

	instruction_type: InstructionType
	rd: int
	rs1: int
	rs2: int
	imm: Any
	do_not_optimize: bool

	def __init__(self, instruction_type: InstructionType, rd: int, rs1: int, rs2: int, imm: Any, do_not_optimize: bool):
		self.instruction_type = instruction_type
		self.rd = rd
		self.rs1 = rs1
		self.rs2 = rs2
		self.imm = imm
		self.do_not_optimize = do_not_optimize
	
	def __str__(self):
		return f"{self.instruction_type.name}  {self.rd}  {self.rs1} {self.rs2}  [{self.imm}]  {self.do_not_optimize}"

REG_NONE = 0
REG_RET = 8

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
	
	def write_constant_int(self, rd: int, value: int):
		self.instructions.append(Instruction(InstructionType.CONST_INT, rd, REG_NONE, REG_NONE, value, False))
	
	def output_constant_int(self, inst: Instruction, file_out: TextIOWrapper):
		file_out.write(f"li {self._reg(inst.rd)} {inst.imm}\n")
	
	def write_global_addr_load(self, rd: int, value: str):
		self.instructions.append(Instruction(InstructionType.GLOBAL_ADDR_LOAD, rd, REG_NONE, REG_NONE, value, False))
	
	def output_global_addr_load(self, inst: Instruction, file_out: TextIOWrapper):
		file_out.write(f"li {self._reg(inst.rd)} {inst.imm}\n")

	def write_arg_store(self, value: int, offset: int, locals_size: int):
		self.instructions.append(Instruction(InstructionType.ARG_STORE, REG_NONE, value, REG_NONE, (offset, locals_size), True))
	
	def output_arg_store(self, inst: Instruction, file_out: TextIOWrapper):
		arg_offset = 4 + inst.imm[1] + self.temporaries_count * 4 + inst.imm[0]
		file_out.write(f"sw {self._reg(inst.rs1)} -{arg_offset}(fp)\n")

	def write_local_load(self, rd: int, offset: int, size: int, signed: bool):
		self.instructions.append(Instruction(InstructionType.LOCAL_LOAD, rd, REG_NONE, REG_NONE, (offset, size, signed), False))
	
	def output_local_load(self, inst: Instruction, file_out: TextIOWrapper):
		file_out.write(f"l{self._mem_access(inst.imm[1], inst.imm[2])} {self._reg(inst.rd)} -{4 + inst.imm[0]}(fp)\n")
	
	def write_local_store(self, value: int, offset: int, size: int, signed: bool):
		self.instructions.append(Instruction(InstructionType.LOCAL_STORE, REG_NONE, value, REG_NONE, (offset, size, signed), True))
	
	def output_local_store(self, inst: Instruction, file_out: TextIOWrapper):
		file_out.write(f"s{self._mem_access(inst.imm[1], inst.imm[2])} {self._reg(inst.rs1)} -{4 + inst.imm[0]}(fp)\n")

	def write_nested_local_load(self, rd: int, fp: int, offset: int):
		self.instructions.append(Instruction(InstructionType.NESTED_LOCAL_LOAD, rd, REG_NONE, fp, offset, False))
	
	def output_nested_local_load(self, inst: Instruction, file_out: TextIOWrapper):
		file_out.write(f"l{self._mem_access(inst.imm[1], inst.imm[2])} {self._reg(inst.rd)} -{4 + inst.imm[0]}({self._reg(inst.rs2)})\n")

	def write_nested_local_store(self, value: int, fp: int, offset: int):
		self.instructions.append(Instruction(InstructionType.NESTED_LOCAL_STORE, REG_NONE, value, fp, offset, True))
	
	def output_nested_local_store(self, inst: Instruction, file_out: TextIOWrapper):
		file_out.write(f"l{self._mem_access(inst.imm[1], inst.imm[2])} {self._reg(inst.rs1)} -{4 + inst.imm[0]}({self._reg(inst.rs2)})\n")

	def write_load_fp(self, rd: int):
		self.instructions.append(Instruction(InstructionType.LOAD_FP, rd, REG_NONE, REG_NONE, 0, False))
	
	def write_nested_load_fp(self, rd: int, fp: int):
		self.instructions.append(Instruction(InstructionType.NESTED_LOAD_FP, rd, fp, REG_NONE, 0, False))
	
	def write_load_static_link(self, rd: int):
		self.instructions.append(Instruction(InstructionType.LOAD_STATIC_LINK, rd, REG_NONE, REG_NONE, 0, False))
	
	def write_nested_load_static_link(self, rd: int, fp: int):
		self.instructions.append(Instruction(InstructionType.NESTED_LOAD_STATIC_LINK, rd, fp, REG_NONE, 0, False))

	def write_global_load(self, rd: int, symbol: str, size: int, signed: bool):
		self.instructions.append(Instruction(InstructionType.GLOBAL_LOAD, rd, REG_NONE, REG_NONE, (symbol, size, signed), False))

	def output_global_load(self, inst: Instruction, file_out: TextIOWrapper):
		file_out.write(f"li t15 ${inst.imm[0]}\n")
		file_out.write(f"l{self._mem_access(inst.imm[1], inst.imm[2])} {inst.rs1} 0(t15)\n")

	def write_global_store(self, value: int, symbol: str, size: int, signed: bool):
		self.instructions.append(Instruction(InstructionType.GLOBAL_STORE, REG_NONE, value, REG_NONE, (symbol, size, signed), True))
	
	def output_global_store(self, inst: Instruction, file_out: TextIOWrapper):
		file_out.write(f"li t15 ${inst.imm[0]}\n")
		file_out.write(f"s{self._mem_access(inst.imm[1], inst.imm[2])} {inst.rs1} 0(t15)\n")

	def write_call(self, rd: int, func_addr: int, locals_size: int, args_size: int):
		self.instructions.append(Instruction(InstructionType.CALL, rd, func_addr, REG_NONE, (0, locals_size, args_size), True))
	
	def output_call(self, inst: Instruction, file_out: TextIOWrapper):
		saved_fp_offset = 4 + inst.imm[1] + self.temporaries_count * 4 + inst.imm[2]
		static_link_offset = saved_fp_offset + 4
		new_fp_offset = static_link_offset + 4
		file_out.write(f"sw fp -{saved_fp_offset}(fp)\n")
		file_out.write(f"sw fp -{static_link_offset}(fp)\n") # TODO: Correct static link
		file_out.write(f"addi fp fp -{new_fp_offset}\n")
		file_out.write(f"jra ra {self._reg(inst.rs1)}\n")
		file_out.write(f"mv {self._reg(inst.rd)} a0\n")

	def write_call_static(self, rd: int, func_name: str, locals_size: int, args_size: int):
		self.instructions.append(Instruction(InstructionType.CALL_STATIC, rd, REG_NONE, REG_NONE, (func_name, locals_size, args_size), True))
	
	def output_call_static(self, inst: Instruction, file_out: TextIOWrapper):
		saved_fp_offset = 4 + inst.imm[1] + self.temporaries_count * 4 + inst.imm[2]
		static_link_offset = saved_fp_offset + 4
		new_fp_offset = static_link_offset + 4
		file_out.write(f"sw fp -{saved_fp_offset}(fp)\n")
		file_out.write(f"sw fp -{static_link_offset}(fp)\n") # TODO: Correct static link
		file_out.write(f"addi fp fp -{new_fp_offset}\n")
		file_out.write(f"ja ra {inst.imm[0]}\n")
		file_out.write(f"mv {self._reg(inst.rd)} a0\n")

	def write_load_static_func_addr(self, rd: int, func_name: str):
		self.instructions.append(Instruction(InstructionType.LOAD_STATIC_FUNC_ADDR, rd, REG_NONE, REG_NONE, func_name, False))

	def write_ret(self, value: int):
		self.instructions.append(Instruction(InstructionType.RET, REG_NONE, value, REG_NONE, 0, True))
	
	def output_ret(self, inst: Instruction, file_out: TextIOWrapper):
		file_out.write(f"mv a0 {self._reg(inst.rs1)}\n")
		self.output_ret_void(inst, file_out)

	def write_ret_void(self):
		self.instructions.append(Instruction(InstructionType.RET_VOID, REG_NONE, REG_NONE, REG_NONE, 0, True))
	
	def output_ret_void(self, inst: Instruction, file_out: TextIOWrapper):
		file_out.write(f"lw ra 0(fp)\n")
		file_out.write(f"lw fp 8(fp)\n")
		file_out.write(f"jra zero ra\n")
	
	def write_inline_asm(self, asm: str):
		self.instructions.append(Instruction(InstructionType.INLINE_ASM, REG_NONE, REG_NONE, REG_NONE, asm, True))
	
	def output_inline_asm(self, inst: Instruction, file_out: TextIOWrapper):
		file_out.write(f"{inst.imm}\n")

	def write_syscall(self, syscall: int):
		self.instructions.append(Instruction(InstructionType.SYSCALL, REG_NONE, REG_NONE, REG_NONE, syscall, True))
	
	def write_binary_op(self, rd: int, rs1: int, rs2: int, op: str):
		self.instructions.append(Instruction(InstructionType.BINARY_OP, rd, rs1, rs2, op, False))
	
	def output_binary_op(self, inst: Instruction, file_out: TextIOWrapper):
		file_out.write(f"{inst.imm} {self._reg(inst.rd)} {self._reg(inst.rs1)} {self._reg(inst.rs2)}\n")

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
				if inst.rs1 != REG_NONE:
					new_live_vars_in.add(inst.rs1)
				if inst.rs2 != REG_NONE:
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
				if inst.rs1 != REG_NONE:
					live_vars.add(inst.rs1)
				if inst.rs2 != REG_NONE:
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
	InstructionType.CONST_INT: InstructionList.output_constant_int,
	InstructionType.GLOBAL_ADDR_LOAD: InstructionList.output_global_addr_load,
	InstructionType.ARG_STORE: InstructionList.output_arg_store,
	InstructionType.LOCAL_LOAD: InstructionList.output_local_load,
	InstructionType.LOCAL_STORE: InstructionList.output_local_store,
	InstructionType.NESTED_LOCAL_LOAD: InstructionList.output_nested_local_load,
	InstructionType.NESTED_LOCAL_STORE: InstructionList.output_nested_local_store,
	InstructionType.LOAD_FP: print,
	InstructionType.NESTED_LOAD_FP: print,
	InstructionType.LOAD_STATIC_LINK: print,
	InstructionType.NESTED_LOAD_STATIC_LINK: print,
	InstructionType.GLOBAL_LOAD: InstructionList.output_global_load,
	InstructionType.GLOBAL_STORE: InstructionList.output_global_store,
	InstructionType.CALL: InstructionList.output_call,
	InstructionType.CALL_STATIC: InstructionList.output_call_static,
	InstructionType.LOAD_STATIC_FUNC_ADDR: print,
	InstructionType.RET: InstructionList.output_ret,
	InstructionType.RET_VOID: InstructionList.output_ret_void,
	InstructionType.INLINE_ASM: InstructionList.output_inline_asm,
	InstructionType.SYSCALL: print,
	InstructionType.BINARY_OP : InstructionList.output_binary_op,
}