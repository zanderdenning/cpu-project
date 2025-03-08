from util import bin_obj, label

class LinkedFile:

	version: tuple[int, int, int]
	code_global_labels: dict[str, label.Label]
	data_global_labels: dict[str, label.Label]
	relocation_table: list[label.Relocation]
	data_section: bytes
	instructions: list[int]
	data_start: int
	instructions_start: int

	def __init__(self, version: tuple[int, int, int], code_global_labels: dict[str, label.Label], data_global_labels: dict[str, label.Label], relocation_table: list[label.Relocation], data_section: bytes, instructions: list[int]):
		self.version = version
		self.code_global_labels = code_global_labels
		self.data_global_labels = data_global_labels
		self.relocation_table = relocation_table
		self.data_section = data_section
		self.instructions = instructions
		self.data_start = 0
		self.instructions_start = 0

class Linker:

	files: list[LinkedFile]
	global_labels: dict[str, label.Label]
	data_section: bytearray
	instructions: list[int]

	def __init__(self):
		self.files = []
		self.global_labels = {}
		self.data_section = bytearray()
		self.instructions = []

	def link_files(self, input_files: list[str], output_file: str):
		for input_file in input_files:
			with open(input_file, "rb") as buffer:
				version, code_global_labels_start, data_global_labels_start, relocation_table_start, data_start, data_length, instructions_start, instruction_count = bin_obj.parse_obj_header(buffer)
				buffer.seek(code_global_labels_start)
				code_global_labels = bin_obj.parse_labels_section(buffer)
				buffer.seek(data_global_labels_start)
				data_global_labels = bin_obj.parse_labels_section(buffer)
				buffer.seek(relocation_table_start)
				relocation_table = bin_obj.parse_relocation_section(buffer)
				buffer.seek(data_start)
				data_section = buffer.read(data_length)
				buffer.seek(instructions_start)
				instructions = bin_obj.parse_code_section(buffer, instruction_count)
				self.files.append(LinkedFile(version, code_global_labels, data_global_labels, relocation_table, data_section, instructions))
		
		current_pos = bin_obj.EXE_HEADER_LENGTH + bin_obj.EXE_START_ADDR
		for file in self.files:
			file.data_start = current_pos
			current_pos += len(file.data_section)
		instructions_start = current_pos
		for file in self.files:
			file.instructions_start = current_pos
			current_pos += len(file.instructions) * 4
		
		for file in self.files:
			for l in file.code_global_labels.values():
				l.offset += file.instructions_start
				if l.scope == label.LabelScope.GLOBAL:
					self.global_labels[l.name] = l
			for l in file.data_global_labels.values():
				l.offset += file.data_start
				if l.scope == label.LabelScope.GLOBAL:
					self.global_labels[l.name] = l
		
		for file in self.files:
			self.instructions += file.instructions
			self.data_section.extend(file.data_section)
		
		for file in self.files:
			for relocation in file.relocation_table:
				value = 0
				relocation.offset += file.instructions_start
				if relocation.symbol in file.code_global_labels:
					value = file.code_global_labels[relocation.symbol].offset
				elif relocation.symbol in file.data_global_labels:
					value = file.data_global_labels[relocation.symbol].offset
				elif relocation.symbol in self.global_labels:
					value = self.global_labels[relocation.symbol].offset
				else:
					raise RuntimeError(f"Cannot find label {relocation.symbol}")
				if relocation.relative:
					value = value - relocation.offset
				mask = (1 << relocation.bit_len) - 1
				value >>= relocation.bit_shift
				value &= mask
				value <<= relocation.bit_offset
				mask = ~(mask << relocation.bit_offset) & 0xFFFFFFFF
				self.instructions[(relocation.offset - instructions_start) >> 2] = (self.instructions[(relocation.offset - instructions_start) >> 2] & mask) | value
		
		with open(output_file, "wb") as out_file:
			code_section = bin_obj.generate_code_section(self.instructions)
			data_section = self.data_section
			main = self.global_labels.get("$main").offset
			data_start = bin_obj.EXE_HEADER_LENGTH
			code_start = data_start + len(data_section)
			header = bin_obj.generate_exe_header(self.files[0].version, code_start, len(self.instructions), data_start, len(data_section), main)

			out_file.write(header)
			out_file.write(data_section)
			out_file.write(code_section)