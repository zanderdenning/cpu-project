from enum import IntEnum

class LabelScope(IntEnum):

	GLOBAL = 0
	LOCAL = 1

class Label:

	name: str
	scope: LabelScope
	offset: int

	def __init__(self, name: str, scope: LabelScope, offset: int):
		self.name = name
		self.scope = scope
		self.offset = offset

class Relocation:

	symbol: str
	offset: int
	bit_offset: int
	bit_len: int
	bit_shift: int
	relative: bool

	def __init__(self, symbol: str, offset: int, bit_offset: int, bit_len: int, bit_shift: int, relative: bool):
		self.symbol = symbol
		self.offset = offset
		self.bit_offset = bit_offset
		self.bit_len = bit_len
		self.bit_shift = bit_shift
		self.relative = relative