from enum import IntEnum

class Opcode(IntEnum):

	RR_ARITHMETIC = 0b0000000
	RI_ARITHMETIC = 0b0000001
	MEM_LOAD = 0b0000010
	MEM_STORE = 0b0000011
	COND_BRANCH = 0b0000100
	JUMP = 0b0000101
	JUMP_REG = 0b0000110
	LOAD_UPPER_IMM = 0b0000111
	FPU_ARITHMETIC = 0b0001000
	CACHE_COMMAND = 0b0001001

class ArithOp(IntEnum):

	ADD = 0b000
	AND = 0b001
	OR = 0b010
	XOR = 0b011
	SLL = 0b100
	SEQ = 0b101
	SLT = 0b110
	SLTU = 0b111

ARITH_OP_MAP = {
	"add": (ArithOp.ADD, 0b000),
	"sub": (ArithOp.ADD, 0b001),
	"and": (ArithOp.AND, 0b000),
	"or": (ArithOp.OR, 0b000),
	"xor": (ArithOp.XOR, 0b000),
	"sll": (ArithOp.SLL, 0b000),
	"srl": (ArithOp.SLL, 0b001),
	"sra": (ArithOp.SLL, 0b011),
	"rl": (ArithOp.SLL, 0b100),
	"rr": (ArithOp.SLL, 0b101),
	"seq": (ArithOp.SEQ, 0b000),
	"slt": (ArithOp.SLT, 0b000),
	"sltu": (ArithOp.SLTU, 0b000),
	"addi": (ArithOp.ADD, 0b000),
	"andi": (ArithOp.AND, 0b000),
	"ori": (ArithOp.OR, 0b000),
	"xori": (ArithOp.XOR, 0b000),
	"slli": (ArithOp.SLL, 0b000),
	"srli": (ArithOp.SLL, 0b001),
	"srai": (ArithOp.SLL, 0b011),
	"rli": (ArithOp.SLL, 0b100),
	"rri": (ArithOp.SLL, 0b101),
	"seqi": (ArithOp.SEQ, 0b000),
	"slti": (ArithOp.SLT, 0b000),
	"sltui": (ArithOp.SLTU, 0b000),
}

BRANCH_COND_MAP = {
	"blt": 0b0001,
	"ble": 0b0011,
	"beq": 0b0010,
	"bne": 0b0101,
	"bgt": 0b0100,
	"bge": 0b0110,
	"bltu": 0b1001,
	"bleu": 0b1011,
	"bgtu": 0b1100,
	"bgeu": 0b1110,
}

MEM_LOAD_OP_MAP = {
	"lw": 0b111,
	"lh": 0b101,
	"lhu": 0b001,
	"lb": 0b100,
	"lbu": 0b000,
}

MEM_STORE_OP_MAP = {
	"sw": 0b111,
	"sh": 0b101,
	"sb": 0b100,
}