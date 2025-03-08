import io
import struct

from util import label

OBJ_HEADER_LENGTH = 36
EXE_HEADER_LENGTH = 28
EXE_START_ADDR = 0x80

def generate_obj_header(version: tuple[int, int, int], code_global_labels_start: int, data_global_labels_start: int, relocation_table_start: int, data_start: int, data_length: int, instructions_start: int, instruction_count: int) -> bytes:
	return struct.pack(
		"<ccccBBBxIIIIIII",
		b"O", b"B", b"J", b" ",
		version[0], version[1], version[2],
		code_global_labels_start,
		data_global_labels_start,
		relocation_table_start,
		data_start,
		data_length,
		instructions_start,
		instruction_count
	)

def parse_obj_header(buffer: io.BufferedReader) -> tuple[tuple[int, int, int], int, int, int, int, int, int, int]:
	parts = struct.unpack("<ccccBBBxIIIIIII", buffer.read(OBJ_HEADER_LENGTH))
	if parts[0:4] != (b"O", b"B", b"J", b" "):
		raise RuntimeError("Invalid magic bytes in object header")
	return ((parts[4], parts[5], parts[6]), parts[7], parts[8], parts[9], parts[10], parts[11], parts[12], parts[13])

def generate_exe_header(version: tuple[int, int, int], instructions_start: int, instruction_count: int, data_start: int, data_length: int, main: int) -> bytes:
	return struct.pack(
		"<ccccBBBxIIIII",
		b"E", b"X", b"E", b" ",
		version[0], version[1], version[2],
		instructions_start,
		instruction_count,
		data_start,
		data_length,
		main
	)

def parse_exe_header(buffer: io.BufferedReader) -> tuple[tuple[int, int, int], int, int, int, int, int]:
	parts = struct.unpack("<ccccBBBxIIIII", buffer.read(EXE_HEADER_LENGTH))
	if parts[0:4] != (b"E", b"X", b"E", b" "):
		raise RuntimeError("Invalid magic bytes in executable header")
	return ((parts[4], parts[5], parts[6]), parts[7], parts[8], parts[9], parts[10], parts[11])

def generate_labels_section(labels: dict[str, label.Label]) -> bytes:
	return struct.pack(
		"<I",
		len(labels)
	) + b"".join([struct.pack(
		"<IBB",
		label.offset,
		label.scope,
		len(label.name)
	) + label.name.encode() + bytes((4 - len(label.name) - 2) % 4) for label in labels.values()])

def parse_labels_section(buffer: io.BufferedReader) -> dict[str, label.Label]:
	count, = struct.unpack("<I", buffer.read(4))
	labels = {}
	for _ in range(count):
		offset, scope, name_length = struct.unpack("<IBB", buffer.read(6))
		name = buffer.read(name_length).decode()
		buffer.seek((4 - name_length - 2) % 4, 1)
		labels[name] = label.Label(name, scope, offset)
	return labels

def generate_relocation_section(relocations: list[label.Relocation]) -> bytes:
	return struct.pack(
		"<I",
		len(relocations)
	) + b"".join([struct.pack(
		"<IBBB?B",
		relocation.offset,
		relocation.bit_offset,
		relocation.bit_len,
		relocation.bit_shift,
		relocation.relative,
		len(relocation.symbol)
	) + relocation.symbol.encode() + bytes((4 - len(relocation.symbol) - 1) % 4) for relocation in relocations])

def parse_relocation_section(buffer: io.BufferedReader) -> list[label.Relocation]:
	count, = struct.unpack("<I", buffer.read(4))
	relocations = []
	for _ in range(count):
		offset, bit_offset, bit_len, bit_shift, relative, symbol_length = struct.unpack("<IBBB?B", buffer.read(9))
		symbol = buffer.read(symbol_length).decode()
		buffer.seek((4 - symbol_length - 1) % 4, 1)
		relocations.append(label.Relocation(symbol, offset, bit_offset, bit_len, bit_shift, relative))
	return relocations

def generate_code_section(instructions: list[int]) -> bytes:
	return b"".join([struct.pack(
		"<I",
		inst
	) for inst in instructions])

def parse_code_section(buffer: io.BufferedReader, instuction_count: int) -> list[int]:
	instructions = []
	for _ in range(instuction_count):
		instructions.append(struct.unpack("<I", buffer.read(4))[0])
	return instructions