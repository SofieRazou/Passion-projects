`timescale 1ns/1ps

// =======================
// DUT: top module
// =======================
module top (
    input clk,
    input rst,

    output reg [31:0] PC_out,
    output reg [31:0] instruction_out,
    output reg [31:0] rd1_out,
    output reg [31:0] rd2_out,
    output reg [31:0] alu_result_out,
    output reg [31:0] MemData_out_out
);

    // Dummy CPU logic
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            PC_out          <= 32'b0;
            instruction_out <= 32'h00000013;
            rd1_out         <= 32'b0;
            rd2_out         <= 32'b0;
            alu_result_out  <= 32'b0;
            MemData_out_out <= 32'b0;
        end else begin
            PC_out          <= PC_out + 4;
            instruction_out <= instruction_out + 1;
            rd1_out         <= rd1_out + 1;
            rd2_out         <= rd2_out + 2;
            alu_result_out  <= alu_result_out + 3;
            MemData_out_out <= MemData_out_out + 4;
        end
    end

endmodule


// =======================
// Testbench
// =======================
module tb_top;

    reg clk;
    reg rst;

    wire [31:0] PC_out;
    wire [31:0] instruction_out;
    wire [31:0] rd1_out;
    wire [31:0] rd2_out;
    wire [31:0] alu_result_out;
    wire [31:0] MemData_out_out;

    // Instantiate DUT (FIXED)
    top uut (
        .clk(clk),
        .rst(rst),
        .PC_out(PC_out),
        .instruction_out(instruction_out),
        .rd1_out(rd1_out),
        .rd2_out(rd2_out),
        .alu_result_out(alu_result_out),
        .MemData_out_out(MemData_out_out)
    );

    // Clock generation (10 ns period)
    initial clk = 0;
    always #5 clk = ~clk;

    // Reset + run
    initial begin
        rst = 1;
        #12 rst = 0;
        #200 $finish;
    end

    // VCD dump (FIXED)
    initial begin
        $dumpfile("test_tb.vcd");
        $dumpvars(0, tb_top);
    end

endmodule
