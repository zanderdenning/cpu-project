`timescale 1ns / 1ps

`include "constants.svh"

import types::*;

module cpu_testbench(

);

	localparam CLOCK_PERIOD = 10;

	logic clk;
	initial clk = 1'b0;
	always #(CLOCK_PERIOD / 2.0) begin
		clk = ~clk;
	end

	logic rst;

	logic [127:0] memory [0:(2**`PHYS_MEM_BITS)-1];

	logic [`PHYS_MEM_BITS-1:0] imem_req_addr;
	logic imem_req_valid;

	logic [127:0] imem_resp_data;
	logic imem_resp_ready;
	logic imem_resp_valid;

	core dut(
		.clk(clk), .rst(rst),

		.imem_req_addr(imem_req_addr),
		.imem_req_ready(1'b1),
		.imem_req_valid(imem_req_valid),

		.imem_resp_data(imem_resp_data),
		.imem_resp_ready(imem_resp_ready),
		.imem_resp_valid(imem_resp_valid)
	);

	always_comb begin
		if (imem_req_valid & imem_resp_ready) begin
			imem_resp_data = memory[imem_req_addr];
			imem_resp_valid = 1'b1;
		end
		else begin
			imem_resp_data = 127'b0;
			imem_resp_valid = 1'b0;
		end
	end

	initial begin
		$readmemh("../testbench/ram.mem", memory, 8);
	end

	initial begin
		rst = 1'b1;
		repeat (5) begin
			@(posedge clk);
		end
		rst = 1'b0;
	end

	initial begin
		repeat (200) begin
			@(posedge clk);
		end
		$finish();
	end

endmodule