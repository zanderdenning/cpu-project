`timescale 1ns / 1ps

module icache (
	input logic clk, rst,

	input logic [31:0] req_addr,
	output logic req_ready,
	input logic req_valid,

	output logic [31:0] resp_data,
	input logic resp_ready,
	output logic resp_valid,

	output logic [31:0] ext_mem_req_addr,
	input logic ext_mem_req_ready,
	output logic ext_mem_req_valid,

	input logic [127:0] ext_mem_resp_data,
	output logic ext_mem_resp_ready,
	input logic ext_mem_resp_valid
);

	typedef enum logic {IDLE, FETCH} cache_state_type;

	cache_state_type curr_state, next_state;

	logic [4:0] bram_addr;
	logic [127:0] bram_din;
	logic [127:0] bram_dout;
	logic [22:0] tag_bram_din;
	logic [22:0] tag_bram_dout;

	logic [31:0] valid_bits;

	logic [31:0] split_line [0:3];
	logic [127:0] line_data;
	logic [31:0] last_req_addr;
	logic tag_match;
	logic req_fire, resp_fire, ext_mem_req_fire, ext_mem_resp_fire;
	logic [31:0] saved_resp_data;
	logic saved_resp_valid;
	logic [31:0] pre_latch_resp_data;
	logic pre_latch_resp_valid;
	logic post_fetch;
	logic data_valid;
	logic delayed_req_fire;

	cache_bram bram(
		.clka(clk),
		.ena(1'b1),
		.wea({16{ext_mem_resp_fire}}),
		.addra(bram_addr),
		.dina(bram_din),
		.douta(bram_dout)
	);

	cache_tag_bram tag_bram(
		.clka(clk),
		.ena(1'b1),
		.wea(ext_mem_resp_fire),
		.addra(bram_addr),
		.dina(tag_bram_din),
		.douta(tag_bram_dout)
	);

	assign ext_mem_resp_ready = 1'b1;
	assign ext_mem_req_addr = last_req_addr;

	assign req_ready = curr_state == IDLE && next_state == IDLE && ~saved_resp_valid;

	assign tag_match = tag_bram_dout == last_req_addr[31:9];
	assign data_valid = valid_bits[last_req_addr[8:4]] & tag_match;

	assign bram_din = ext_mem_resp_data;
	assign tag_bram_din = last_req_addr[31:9];

	assign req_fire = req_ready & req_valid;
	assign resp_fire = resp_ready & resp_valid;
	assign ext_mem_req_fire = ext_mem_req_ready & ext_mem_req_valid;
	assign ext_mem_resp_fire = ext_mem_resp_ready & ext_mem_resp_valid;

	assign {split_line[3], split_line[2], split_line[1], split_line[0]} = line_data;

	assign resp_valid = saved_resp_valid | pre_latch_resp_valid;
	assign resp_data = saved_resp_valid ? saved_resp_data : pre_latch_resp_data;

	always_comb begin
		next_state = curr_state;
		case (curr_state)
			IDLE : begin
				line_data = bram_dout;
				pre_latch_resp_data = split_line[last_req_addr[3:2]];
				pre_latch_resp_valid = delayed_req_fire & data_valid & ~post_fetch;
				bram_addr = req_addr[8:4];
				if (delayed_req_fire & ~data_valid) begin
					next_state = FETCH;
				end
			end
			FETCH : begin
				line_data = ext_mem_resp_data;
				pre_latch_resp_data = split_line[last_req_addr[3:2]];
				pre_latch_resp_valid = ext_mem_resp_fire;
				bram_addr = last_req_addr[8:4];
				if (ext_mem_req_fire) begin
					next_state = IDLE;
				end
			end
		endcase
	end

	always_ff @(posedge clk) begin
		if (rst) begin
			curr_state <= IDLE;
			valid_bits <= 32'b0;
			saved_resp_valid <= 1'b0;
			ext_mem_req_valid <= 1'b0;
			post_fetch <= 1'b0;
			delayed_req_fire <= 1'b0;
		end
		else begin
			curr_state <= next_state;
			post_fetch <= curr_state == FETCH;
			delayed_req_fire <= req_fire;

			if (saved_resp_valid) begin
				if (resp_fire) begin
					saved_resp_valid <= 1'b0;
				end
			end
			else if (~resp_fire) begin
				saved_resp_valid <= pre_latch_resp_valid;
				saved_resp_data <= pre_latch_resp_data;
			end

			if (next_state == IDLE) begin
				last_req_addr <= req_addr;
			end

			if (ext_mem_resp_fire) begin
				valid_bits[last_req_addr[8:4]] <= 1'b1;
			end

			if (ext_mem_req_fire) begin
				ext_mem_req_valid <= 1'b0;
			end
			else if (curr_state == IDLE && next_state == FETCH) begin
				ext_mem_req_valid <= 1'b1;
			end
		end
	end

endmodule