`timescale 1ns / 1ps

module cpu_testbench(

);

	localparam CLOCK_PERIOD = 10;

	logic clk;
	initial clk = 1'b0;
	always #(CLOCK_PERIOD / 2.0) begin
		clk = ~clk;
	end

	reg [31:0] value;

	initial begin
		value = 2;
		#200;
		value = 3;
		$finish();
	end

endmodule