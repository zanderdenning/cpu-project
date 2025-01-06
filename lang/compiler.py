from collections import deque
from io import TextIOWrapper
from typing import Any

from lang import astnode, lexer, parser, scope, types

BUILTIN_TYPE_ALIASES = {
	"void": types.VOID_TYPE,
	"int": types.INT32_TYPE,
	"int32": types.INT32_TYPE,
	"uint32": types.UINT32_TYPE,
	"char": types.CHAR_TYPE,
}

BUILTIN_SYMBOLS = {
	"__asm": (types.FunctionType(types.VOID_TYPE, [types.STRING_TYPE]), scope.VarLocation.BUILTIN),
	"__reg_load_value": (types.FunctionType(types.VOID_TYPE, [types.STRING_TYPE, types.VOID_TYPE]), scope.VarLocation.BUILTIN),
	"__reg_store_value": (types.FunctionType(types.VOID_TYPE, [types.STRING_TYPE, types.VOID_TYPE]), scope.VarLocation.BUILTIN),
	"__size": (types.FunctionType(types.UINT32_TYPE, [types.VOID_TYPE]), scope.VarLocation.BUILTIN),
	"__syscall": (types.FunctionType(types.VOID_TYPE, [types.INT32_TYPE]), scope.VarLocation.BUILTIN),
}

class Compiler:

	def compile(self, path: str, out_path: str):
		source = ""
		with open(path, "r") as file:
			source = file.read()
		tokens = self.lex(source)
		with open(out_path, "w") as out_file:
			program = self.parse(tokens, out_file)

	def lex(self, string: str) -> deque[tuple[parser.Token, Any]]:
		return lexer.Lexer().lex_string(string)
	
	def parse(self, tokens: deque[tuple[parser.Token, Any]], file_out: TextIOWrapper) -> astnode.Program:
		builtin_scope = scope.Scope(None, True, False, False, None)
		builtin_scope.local_types = BUILTIN_TYPE_ALIASES
		builtin_scope.local_vars = BUILTIN_SYMBOLS
		return parser.Parser(tokens, builtin_scope, file_out).parse_program()