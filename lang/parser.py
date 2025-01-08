from binascii import hexlify
from collections import deque
from enum import auto, Enum, IntEnum
from io import TextIOWrapper
from typing import Any, cast

from lang import ilang, scope, types

class Token(Enum):

	EOF = auto()
	PAREN_OPEN = auto()
	PAREN_CLOSE = auto()
	CBRACE_OPEN = auto()
	CBRACE_CLOSE = auto()
	COMMA = auto()
	SEMICOLON = auto()

	EQUALS_ASSIGN = auto()

	PLUS = auto()
	MINUS = auto()
	STAR = auto()
	SLASH = auto()
	PERCENT = auto()

	INTEGER = auto()
	STRING = auto()

	IDENTIFIER = auto()

	PACKAGE = auto()
	RETURN = auto()
	TRUE = auto()
	FALSE = auto()
	NULL = auto()

class Precedence(IntEnum):

	TOP = auto()
	ADDITION = auto()
	MULTIPLICATION = auto()
	CALL = auto()

class Parser():

	tokens: deque[tuple[Token, Any]]
	scopes: deque[scope.Scope]
	functions: deque[tuple[str, ilang.InstructionList]]
	completed_functions: dict[str, ilang.InstructionList]
	current_scope: scope.Scope
	current_function: ilang.InstructionList
	string_pool: set[str]
	out_file: TextIOWrapper
	
	def __init__(self, tokens: deque[tuple[Token, Any]], builtin_scope: scope.Scope, out_file: TextIOWrapper):
		self.tokens = tokens
		self.scopes = deque([builtin_scope])
		self.functions = deque()
		self.completed_functions = {}
		self.current_scope = builtin_scope
		self.current_function = None
		self.string_pool = set()
		self.out_file = out_file
	
	def consume_token(self, expected: Token) -> Any:
		token = self.tokens.popleft()
		token_type = token[0]
		if token_type != expected:
			self.tokens.appendleft(token)
			self.error()
		return token[1]
	
	def match_token(self, expected: Token) -> bool:
		token = self.tokens[0]
		token_type = token[0]
		if token_type == expected:
			return True
		return False
	
	def pop_token(self):
		self.tokens.popleft()
	
	def peek_token(self) -> tuple[Token, Any]:
		return self.tokens[0]

	def is_type_name(self, symbol: str) -> bool:
		if self.current_scope.lookup_local_type(symbol) != None:
			return True
		return False
	
	def push_scope(self, is_function: bool, return_type: types.Type | None):
		self.scopes.append(scope.Scope(self.scopes[-1], False, False, is_function, return_type))
		self.current_scope = self.scopes[-1]

	def pop_scope(self) -> scope.Scope:
		out = self.scopes.pop()
		self.current_scope = self.scopes[-1]
		return out
	
	def push_function(self, function_path: str, function_type: types.FunctionType):
		self.functions.append((function_path, ilang.InstructionList(function_type)))
		self.current_function = self.functions[-1][1]
	
	def pop_function(self) -> tuple[str, ilang.InstructionList]:
		out = self.functions.pop()
		self.current_function = None if len(self.functions) == 0 else self.functions[-1][1]
		return out
	
	def error(self):
		raise RuntimeError(f"Unexpected token {self.peek_token()}")
	
	def parse_program(self):
		self.out_file.write(f".section code\n")
		self.consume_token(Token.PACKAGE)
		package_name = self.consume_token(Token.IDENTIFIER)
		self.consume_token(Token.SEMICOLON)

		self.push_scope(False, None)
		self.current_scope.is_global = True

		statements = []
		while not self.match_token(Token.EOF):
			statements.append(self.parse_statement(True, False))
		self.pop_token()
		
		self.out_file.write(f".section data\n")

		global_scope = self.pop_scope()

		current_offset = 0
		global_scope.add_local_var("", types.VOID_TYPE)
		for global_var in global_scope.local_var_offsets:
			new_offset = global_scope.local_var_offsets[global_var]
			self.out_file.write(f".padding {new_offset - current_offset}\n")
			if global_var == "":
				break
			self.out_file.write(f".global ${global_var}:\n")
			current_offset = new_offset

		for string in self.string_pool:
			self.out_file.write(f"str_{hash(string) & 0xFFFFFFFF}:\n")
			self.out_file.write(f".bytes {hexlify(string.encode()).decode()}\n")
			padding = (4 - len(string)) % 4
			if padding != 0:
				self.out_file.write(f".padding {padding}\n")
	
	# Types and Identifiers
	
	def parse_type_annotation(self) -> types.Type:
		symbol = self.parse_decl_identifier()
		current_type = self.current_scope.lookup_local_type(symbol)
		while self.match_token(Token.STAR):
			self.pop_token()
			current_type = types.PointerType(current_type)
		return current_type
	
	def parse_decl_identifier(self) -> str:
		return self.consume_token(Token.IDENTIFIER)
	
	# Declarations
	
	def parse_statement(self, allow_declarations: bool, allow_non_declarations: bool):
		if self.match_token(Token.IDENTIFIER):
			_, id = self.peek_token()
			if self.is_type_name(id):
				if allow_declarations:
					self.parse_declaration()
				else:
					self.error()
				return
		elif self.match_token(Token.RETURN):
			if allow_non_declarations:
				self.parse_return_statement()
			else:
				self.error()
			return
		self.parse_expression_statement()
	
	def parse_declaration(self):
		decl_type = self.parse_type_annotation()
		decl_name = self.parse_decl_identifier()
		if self.match_token(Token.PAREN_OPEN):
			self.parse_func_def(decl_type, decl_name)
		elif self.match_token(Token.SEMICOLON):
			self.parse_var_decl(decl_type, decl_name)
	
	def parse_func_def(self, return_type: types.Type, name: str):
		self.pop_token()
		params = []
		param_types = []
		if not self.match_token(Token.PAREN_CLOSE):
			while True:
				param_type = self.parse_type_annotation()
				param_name = self.parse_decl_identifier()
				params.append((param_name, param_type))
				param_types.append(param_type)
				if self.match_token(Token.PAREN_CLOSE):
					break
				self.consume_token(Token.COMMA)
		self.consume_token(Token.PAREN_CLOSE)
		function_type = types.FunctionType(return_type, param_types)
		self.current_scope.local_vars[name] = (function_type, scope.VarLocation.STATIC_FUNCTION)
		self.consume_token(Token.CBRACE_OPEN)
		self.push_scope(True, return_type)
		self.push_function(name, function_type)
		for param_name, param_type in params:
			self.current_scope.local_vars[param_name] = (param_type, scope.VarLocation.ARG)
		while not self.match_token(Token.CBRACE_CLOSE):
			self.parse_statement(True, True)
		self.current_function.write_ret_void()
		func_scope = self.pop_scope()
		func_path, func_body = self.pop_function()
		if self.current_scope.is_global:
			func_path = f"${func_path}"
		print()
		print(func_path)
		for i in func_body.instructions:
			print(i)
		self.out_file.write(f".global {func_path}:\n")
		self.out_file.write(f"sw ra 0(fp)\n")
		func_body.generate_code(self.out_file)

		# TODO: Output function body
		self.consume_token(Token.CBRACE_CLOSE)
	
	def parse_var_decl(self, var_type: types.Type, name: str):
		self.consume_token(Token.SEMICOLON)
		self.current_scope.add_local_var(name, var_type)
	
	# Other statements

	def parse_expression_statement(self):
		self.parse_expression_top_level()
		self.consume_token(Token.SEMICOLON)
	
	def parse_return_statement(self):
		self.consume_token(Token.RETURN)
		return_type = self.current_scope.get_return_type()
		if self.match_token(Token.SEMICOLON):
			self.pop_token()
			if not types.can_assign_to(types.VOID_TYPE, return_type):
				self.error()
			self.current_function.write_ret_void()
			return

		expr_type, expr_rs = self.parse_expression_top_level()
		if not types.can_assign_to(expr_type, return_type):
			self.error()
		self.current_function.write_ret(expr_rs)
		self.consume_token(Token.SEMICOLON)

	# Expressions

	def parse_expression_top_level(self) -> tuple[types.Type, int]:
		return self.parse_expression(Precedence.TOP)
	
	def parse_expression(self, precedence: int) -> tuple[types.Type, int]:
		first_token_type, _ = self.peek_token()
		prefix_parser = _PREFIX_PARSERS.get(first_token_type)
		if prefix_parser == None:
			self.error()
		left = prefix_parser(self)
		while True:
			first_token_type, _ = self.peek_token()
			infix_parser, parser_precedence = _INFIX_PARSERS.get(first_token_type, (None, 0))
			if precedence >= parser_precedence:
				break
			left = infix_parser(self, left, parser_precedence)
		return left

	def parse_identifier(self) -> tuple[types.Type, int]:
		symbol = self.consume_token(Token.IDENTIFIER)
		var_type, depth, var_scope, location = self.current_scope.lookup_local_var(symbol)
		if var_type == None:
			self.error()
		type_size = types.get_type_size(var_type)
		type_signed = types.is_type_signed(var_type)
		if depth == -2:
			builtin_function = _BUILTIN_FUNCTIONS.get(symbol)
			if builtin_function != None:
				return builtin_function(self)
			self.error()
		if depth == -1:
			symbol = f"${symbol}"
		
		if location == scope.VarLocation.STATIC_FUNCTION:
			if self.match_token(Token.PAREN_OPEN):
				return self.parse_static_func_call(symbol, var_type)
			else:
				rd = self.current_function.get_register()
				self.current_function.write_global_addr_load(rd, symbol)
				return (var_type, rd)
		
		if self.match_token(Token.EQUALS_ASSIGN):
			self.pop_token()
			expr_type, expr_rs = self.parse_expression_top_level()
			if not types.can_assign_to(expr_type, var_type):
				self.error()
			if depth == -1:
				self.current_function.write_global_store(expr_rs, symbol, type_size)
			elif depth == 0:
				self.current_function.write_local_store(expr_rs, var_scope.get_local_offset(symbol), type_size)
			else:
				fp_rd = self.current_function.get_register()
				self.current_function.write_load_static_link(fp_rd)
				for _ in range(1, depth):
					self.current_function.write_nested_load_static_link(fp_rd, fp_rd)
				self.current_function.write_nested_local_store(expr_rs, fp_rd, var_scope.get_local_offset(symbol), type_size)
			return (expr_type, expr_rs)
		
		rd = self.current_function.get_register()
		if depth == -1:
			self.current_function.write_global_load(rd, symbol, type_size, type_signed)
		elif depth == 0:
			self.current_function.write_local_load(rd, var_scope.get_local_offset(symbol), type_size, type_signed)
		else:
			fp_rd = self.current_function.get_register()
			self.current_function.write_load_static_link(fp_rd)
			for _ in range(1, depth):
				self.current_function.write_nested_load_static_link(fp_rd, fp_rd)
			self.current_function.write_nested_local_load(rd, fp_rd, var_scope.get_local_offset(symbol), type_size, type_signed)
		return (var_type, rd)
	
	def parse_integer_literal(self) -> tuple[types.Type, int]:
		value = self.consume_token(Token.INTEGER)
		rd = self.current_function.get_register()
		self.current_function.write_constant_int(rd, value)
		return (types.INT32_TYPE, rd)
	
	def parse_string_literal(self) -> tuple[types.Type, int]:
		value = self.consume_token(Token.STRING)
		self.string_pool.add(value)
		rd = self.current_function.get_register()
		self.current_function.write_global_addr_load(rd, f"str_{hash(value) & 0xFFFFFFFF}")
		return (types.STRING_TYPE, rd)
	
	def parse_static_func_call(self, name: str, function_type: types.FunctionType) -> tuple[types.Type, int]:
		self.pop_token()
		args_size = self.parse_func_call_args(function_type)
		rd = self.current_function.get_register()
		self.current_function.write_call_static(rd, name, self.current_scope.current_var_offset, args_size)
		return (function_type.return_type, rd)
	
	def parse_func_call(self, left: tuple[types.Type, int], precedence: int) -> tuple[types.Type, int]:
		if left[0].type_type != types.TypeType.FUNCTION:
			self.error()
		function_type = cast(types.FunctionType, left[0])
		self.consume_token(Token.PAREN_OPEN)
		args_size = self.parse_func_call_args(function_type)
		rd = self.current_function.get_register()
		self.current_function.write_call(rd, left[1], self.current_scope.current_var_offset, args_size)
		return (function_type.return_type, rd)
	
	def parse_func_call_args(self, function_type: types.FunctionType) -> int:
		args_count = 0
		if not self.match_token(Token.PAREN_CLOSE):
			while True:
				arg_type, arg_rs = self.parse_expression_top_level()
				if args_count >= len(function_type.param_types):
					self.error()
				if not types.can_assign_to(arg_type, function_type.param_types[args_count]):
					self.error()
				self.current_function.write_arg_store(arg_rs, args_count * 4, self.current_scope.current_var_offset)
				args_count += 1
				if self.match_token(Token.PAREN_CLOSE):
					break
				self.consume_token(Token.COMMA)
		self.consume_token(Token.PAREN_CLOSE)
		return args_count * 4
	
	def parse_binary_op(self, left: tuple[types.Type, int], precedence: int) -> tuple[types.Type, int]:
		op = self.tokens.popleft()[0]
		right = self.parse_expression(precedence)
		rd = self.current_function.get_register()
		if op == Token.PLUS:
			self.current_function.write_binary_op(rd, left[1], right[1], "add")
			pass # TODO: Actually do stuff
		return (types.INT32_TYPE, rd) # TODO: Fix the type
	
	# Builtin functions

	def parse_builtin_func_asm(self) -> tuple[types.Type, int]:
		self.consume_token(Token.PAREN_OPEN)
		asm = self.consume_token(Token.STRING)
		self.consume_token(Token.PAREN_CLOSE)
		self.current_function.write_inline_asm(asm)
		return (types.VOID_TYPE, ilang.REG_NONE)
	
	def parse_builtin_func_size(self) -> tuple[types.Type, int]:
		self.consume_token(Token.PAREN_OPEN)
		type_arg = self.parse_type_annotation()
		self.consume_token(Token.PAREN_CLOSE)
		rd = self.current_function.get_register()
		self.current_function.write_constant_int(rd, types.get_type_size(type_arg))
		return (types.UINT32_TYPE, rd)

	def parse_builtin_func_syscall(self) -> tuple[types.Type, int]:
		self.consume_token(Token.PAREN_OPEN)
		syscall = self.consume_token(Token.INTEGER)
		self.consume_token(Token.PAREN_CLOSE)
		self.current_function.write_syscall(syscall)
		return (types.VOID_TYPE, ilang.REG_NONE)

_BUILTIN_FUNCTIONS = {
	"__asm": Parser.parse_builtin_func_asm,
	"__size": Parser.parse_builtin_func_size,
	"__syscall": Parser.parse_builtin_func_syscall,
}

_PREFIX_PARSERS = {
	Token.IDENTIFIER: Parser.parse_identifier,
	Token.INTEGER: Parser.parse_integer_literal,
	Token.STRING: Parser.parse_string_literal,
}

_INFIX_PARSERS = {
	Token.PAREN_OPEN: (Parser.parse_func_call, Precedence.CALL),
	Token.PLUS: (Parser.parse_binary_op, Precedence.ADDITION),
	Token.MINUS: (Parser.parse_binary_op, Precedence.ADDITION),
	Token.STAR: (Parser.parse_binary_op, Precedence.MULTIPLICATION),
	Token.SLASH: (Parser.parse_binary_op, Precedence.MULTIPLICATION),
	Token.PERCENT: (Parser.parse_binary_op, Precedence.MULTIPLICATION),
}