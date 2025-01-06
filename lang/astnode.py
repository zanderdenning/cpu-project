from enum import Enum, auto

from lang import scope, types

class NodeType(Enum):

	PROGRAM = auto()

	TYPE_ANNOTATION_TYPE = auto()
	TYPE_ANNOTATION_POINTER = auto()
	TYPED_IDENTIFIER = auto()

	FUNC_DEF = auto()
	EXPRESSION_STATEMENT = auto()
	RETURN_STATEMENT = auto()
	BLOCK = auto()

	IDENTIFIER = auto()
	FUNC_CALL = auto()

	INTEGER_LITERAL = auto()
	STRING_LITERAL = auto()

class AstNode:

	node_type: NodeType

class Program(AstNode):

	package: str
	statements: list["Statement"]
	local_scope: scope.Scope

	def __init__(self, package: str, statements: list["Statement"], local_scope: scope.Scope):
		self.node_type = NodeType.PROGRAM
		self.package = package
		self.statements = statements
		self.local_scope = local_scope

class TypedIdentifier(AstNode):

	type_annotation: types.Type
	symbol: "Identifier"

	def __init__(self, type_annotation: types.Type, symbol: "Identifier"):
		self.node_type = NodeType.TYPED_IDENTIFIER
		self.type_annotation = type_annotation
		self.symbol = symbol

class Statement(AstNode):

	pass

class FuncDef(Statement):

	identifier: TypedIdentifier
	params: list[TypedIdentifier]
	body: "Block"
	local_scope: scope.Scope

	def __init__(self, identifier: TypedIdentifier, params: list[TypedIdentifier], body: "Block", local_scope: scope.Scope):
		self.node_type = NodeType.FUNC_DEF
		self.identifier = identifier
		self.params = params
		self.body = body
		self.local_scope = local_scope

class ExpressionStatement(Statement):

	expression: "Expression"

	def __init__(self, expression: "Expression"):
		self.node_type = NodeType.EXPRESSION_STATEMENT
		self.expression = expression

class ReturnStatement(Statement):

	value: "Expression"

	def __init__(self, value: "Expression"):
		self.node_type = NodeType.RETURN_STATEMENT
		self.value = value

class Block(Statement):

	statements: list[Statement]

	def __init__(self, statements: list[Statement]):
		self.node_type = NodeType.BLOCK
		self.statements = statements

class Expression(AstNode):
	
	type_annotation: types.Type

class Identifier(Expression):

	symbol: str
	
	def __init__(self, symbol: str):
		self.node_type = NodeType.IDENTIFIER
		self.symbol = symbol

class FuncCall(Expression):

	function: Expression
	args: list[Expression]

	def __init__(self, function: Expression, args: list[Expression]):
		self.node_type = NodeType.FUNC_CALL
		self.function = function
		self.args = args

class BinaryExpression(Expression):

	left: Expression
	op: int
	right: Expression

	def __init__(self, left: Expression, op: int, right: Expression):
		self.left = left
		self.op = op
		self.right = right

class IntegerLiteral(Expression):

	value: int

	def __init__(self, value: int):
		self.node_type = NodeType.INTEGER_LITERAL
		self.value = value

class StringLiteral(Expression):

	value: str

	def __init__(self, value: str):
		self.node_type = NodeType.STRING_LITERAL
		self.value = value