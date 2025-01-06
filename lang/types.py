from enum import auto, Enum, Flag
from typing import cast

class TypeType(Enum):

	PRIMATIVE = auto()
	POINTER = auto()
	FUNCTION = auto()

class Primitive(Flag):

	VOID = auto()
	BYTE = auto()
	HALF = auto()
	WORD = auto()

	UNSIGNED = auto()
	FLOAT = auto()

class Type:

	type_type: TypeType

class PrimitiveType(Type):

	primitive: str

	def __init__(self, primitive: Primitive):
		self.type_type = TypeType.PRIMATIVE
		self.primitive = primitive

class PointerType(Type):

	pointed_type: Type

	def __init__(self, pointed_type: Type):
		self.type_type = TypeType.POINTER
		self.pointed_type = pointed_type

class FunctionType(Type):

	return_type: Type
	param_types: list[Type]

	def __init__(self, return_type: Type, param_types: list[Type]):
		self.type_type = TypeType.FUNCTION
		self.return_type = return_type
		self.param_types = param_types

VOID_TYPE = PrimitiveType(Primitive.VOID)
INT32_TYPE = PrimitiveType(Primitive.WORD)
UINT32_TYPE = PrimitiveType(Primitive.WORD | Primitive.UNSIGNED)
CHAR_TYPE = PrimitiveType(Primitive.BYTE | Primitive.UNSIGNED)
STRING_TYPE = PointerType(CHAR_TYPE)

def get_type_size(t: Type) -> int:
	type_tag = t.type_type
	if type_tag == TypeType.PRIMATIVE:
		primitive = cast(PrimitiveType, t)
		if Primitive.VOID in primitive.primitive:
			return 0
		if Primitive.BYTE in primitive.primitive:
			return 1
		if Primitive.HALF in primitive.primitive:
			return 2
		if Primitive.WORD in primitive.primitive:
			return 4
		raise RuntimeError(f"Bad primitive type {primitive} (unspecified size)")
	if type_tag == TypeType.POINTER:
		return 4
	if type_tag == TypeType.FUNCTION:
		return 4
	return 0

def is_type_signed(t: Type) -> bool:
	type_tag = t.type_type
	if type_tag == TypeType.PRIMATIVE:
		primitive = cast(PrimitiveType, t)
		return Primitive.UNSIGNED not in primitive.primitive
	return False

def align(addr: int, size: int) -> int:
	if size < 2:
		return addr
	if size == 2:
		return (addr + 1) & 0xFFFFFFFFE
	return (addr + 3) & 0xFFFFFFFFC

def can_assign_to(value_type: Type, variable_type: Type) -> bool:
	value_type_tag = value_type.type_type
	variable_type_tag = variable_type.type_type
	if value_type_tag != variable_type_tag:
		return False # TODO: Null, empty list, etc.
	if value_type_tag == TypeType.PRIMATIVE:
		value_primitive = cast(PrimitiveType, value_type)
		variable_primitive = cast(PrimitiveType, variable_type)
		return value_primitive == variable_primitive # TODO: Implicit casting
	if value_type_tag == TypeType.POINTER:
		return can_assign_to(cast(PointerType, value_type).pointed_type, cast(PointerType, variable_type).pointed_type)
	if value_type_tag == TypeType.FUNCTION:
		value_function = cast(FunctionType, value_type)
		variable_function = cast(FunctionType, variable_type)
		if len(value_function.param_types) != len(variable_function.param_types):
			return False
		for i in range(len(value_function.param_types)):
			if not can_assign_to(value_function.param_types[i], variable_function.param_types[i]):
				return False
		return can_assign_to(value_function.return_type, variable_function.return_type)
	return False