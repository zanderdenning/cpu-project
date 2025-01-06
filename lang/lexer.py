from collections import deque
from typing import Any

from lang import parser

class Lexer:

	tokens: deque[tuple[parser.Token, Any]]

	def __init__(self):
		self.tokens = deque()
	
	def lex_string(self, string: str) -> deque[tuple[parser.Token, Any]]:
		idx = 0
		while idx < len(string):
			token, idx = self.get_token(string, idx)
			if token != None:
				self.tokens.append(token)
		self.tokens.append((parser.Token.EOF, None))
		return self.tokens

	def get_token(self, string: str, idx: int) -> tuple[tuple[parser.Token, Any] | None, int]:
		i = idx
		first_char = string[i]
		i += 1

		if first_char.isspace():
			while string[i].isspace():
				i += 1
			return (None, i)

		if first_char == "(":
			return ((parser.Token.PAREN_OPEN, None), i)
		elif first_char == ")":
			return ((parser.Token.PAREN_CLOSE, None), i)
		elif first_char == "{":
			return ((parser.Token.CBRACE_OPEN, None), i)
		elif first_char == "}":
			return ((parser.Token.CBRACE_CLOSE, None), i)
		elif first_char == ",":
			return ((parser.Token.COMMA, None), i)
		elif first_char == ";":
			return ((parser.Token.SEMICOLON, None), i)
		
		elif first_char == "=":
			return ((parser.Token.EQUALS_ASSIGN, None), i)
		
		elif first_char == "+":
			return ((parser.Token.PLUS, None), i)
		elif first_char == "-":
			return ((parser.Token.MINUS, None), i)
		elif first_char == "*":
			return ((parser.Token.STAR, None), i)
		elif first_char == "/":
			return ((parser.Token.SLASH, None), i)
		elif first_char == "%":
			return ((parser.Token.PERCENT, None), i)
		
		elif first_char.isdigit():
			while string[i].isdigit():
				i += 1
			return ((parser.Token.INTEGER, int(string[idx:i])), i)
		elif first_char == "\"":
			while string[i] != "\"":
				i += 1
			return ((parser.Token.STRING, string[idx + 1:i]), i + 1)
		
		elif first_char.isalpha() or first_char == "_":
			while string[i].isalnum() or string[i] == "_":
				i += 1
			return (self.identifier_to_token(string[idx:i]), i)
		
		raise RuntimeError(f"Unexpected token \"{first_char}\"")
	
	def identifier_to_token(self, identifier: str) -> tuple[parser.Token, Any]:
		keyword = _KEYWORDS.get(identifier)
		if keyword != None:
			return (keyword, None)
		return (parser.Token.IDENTIFIER, identifier)

_KEYWORDS = {
	"package": parser.Token.PACKAGE,
	"return": parser.Token.RETURN,
	"true": parser.Token.TRUE,
	"false": parser.Token.FALSE,
	"null": parser.Token.NULL,
}