from collections import OrderedDict
from enum import auto, IntEnum

from lang import types

class VarLocation(IntEnum):

	LOCAL = auto()
	ARG = auto()
	STATIC_FUNCTION = auto()
	BUILTIN = auto()
	MAXIMUM = auto()

class Scope:

	parent: "Scope | None"
	local_types: dict[str, types.Type]
	local_vars: dict[str, tuple[types.Type, VarLocation]]
	current_var_offset: int
	local_var_offsets: OrderedDict[str, int]
	is_builtin: bool
	is_global: bool
	is_function: bool
	return_type: types.Type

	def __init__(self, parent: "Scope | None", is_builtin: bool, is_global: bool, is_function: bool, return_type: types.Type | None):
		self.parent = parent
		self.local_types = {}
		self.local_vars = {}
		self.current_var_offset = 0
		if not is_function and self.parent != None:
			self.current_var_offset = self.parent.current_var_offset
		self.local_var_offsets = OrderedDict()
		self.is_builtin = is_builtin
		self.is_global = is_global
		self.is_function = is_function
		self.return_type = return_type
	
	def add_local_var(self, name: str, var_type: types.Type):
		self.local_vars[name] = (var_type, VarLocation.LOCAL)
		size = types.get_type_size(var_type)
		aligned_addr = types.align(self.current_var_offset, size)
		self.local_var_offsets[name] = aligned_addr
		self.current_var_offset = aligned_addr + size
	
	def lookup_local_type(self, name: str) -> types.Type | None:
		res = self.local_types.get(name)
		if res == None and self.parent != None:
			return self.parent.lookup_local_type(name)
		return res
	
	def lookup_local_var(self, name: str) -> tuple[types.Type | None, int, "Scope", VarLocation]:
		return self.lookup_local_var_depth(name, 0)
	
	def lookup_local_var_depth(self, name: str, depth: int) -> tuple[types.Type | None, int, "Scope", VarLocation]:
		res, location = self.local_vars.get(name, (None, None))
		if res == None and self.parent != None:
			return self.parent.lookup_local_var_depth(name, depth + (1 if self.parent.is_function else 0))
		if self.is_builtin:
			return (res, -2, self, location)
		if self.is_global:
			return (res, -1, self, location)
		return (res, depth, self, location)
	
	def get_return_type(self) -> types.Type:
		if self.is_function:
			return self.return_type
		return self.parent.get_return_type()
	
	def get_local_offset(self, name: str) -> int:
		return self.local_var_offsets[name]