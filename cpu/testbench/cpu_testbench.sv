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

	logic [31:0] memory [(2**`PHYS_MEM_BITS)-1:0];

	mem_resp_interface tb_mem_resp;
	mem_req_interface tb_mem_req;

	top dut(
		.clk(clk), .rst(rst),
		.tb_mem_resp(tb_mem_resp),
		.tb_mem_req(tb_mem_req)
	);

	assign tb_mem_resp.req_ready = 1'b1;

	always_ff @(posedge clk) begin
		tb_mem_resp.read_data <= memory[tb_mem_req.addr];
		tb_mem_resp.resp_valid <= tb_mem_req.ren;
	end

	initial begin
		$readmemh("../testbench/ram.mem", memory, 4);
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