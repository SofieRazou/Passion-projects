// Simple single-cycle style datapath (fixed / completed version)

// programme counter
module counter(
    input clk,
    input rst,
    input  [31:0] PC_in,
    output reg [31:0] PC_out
);
always @(posedge clk or posedge rst) begin
    if (rst)
        PC_out <= 32'b0;
    else
        PC_out <= PC_in;
end
endmodule

// Adder : PC+4
module adder4(
    input  [31:0] fromPC,
    output [31:0] toPC
);
assign toPC = fromPC + 32'd4;
endmodule

// Instruction memory (word addressed: use read_address[7:2] to index 64 words)
module instructionMem(
    input clk,
    input rst,
    input  [31:0] read_address,
    output reg [31:0] inst_write
);
    reg [31:0] IMem [0:63];
    integer k;
    wire [5:0] idx;
    assign idx = read_address[7:2]; // word-aligned index for 64 words

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            for (k = 0; k < 64; k = k + 1) begin
                IMem[k] <= 32'b0;
            end
            inst_write <= 32'b0;
        end
        else begin
            inst_write <= IMem[idx];
        end
    end
endmodule

// Register File
module RegFile(
    input clk,
    input rst,
    input regWrite,
    input [4:0] rs1,
    input [4:0] rs2,
    input [4:0] rd,
    input [31:0] write_data,
    output [31:0] read_data1,
    output [31:0] read_data2
);
    reg [31:0] Regs [0:31];
    integer k;

    // synchronous write, asynchronous read
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            for (k = 0; k < 32; k = k + 1) begin
                Regs[k] <= 32'b0;
            end
        end
        else if (regWrite) begin
            if (rd != 5'd0) // x0 is hardwired to zero in RISC-V
                Regs[rd] <= write_data;
        end
    end

    assign read_data1 = Regs[rs1];
    assign read_data2 = Regs[rs2];
endmodule

// Immediate generator (produces sign-extended immediates)
// opcode selects I-type, S-type, B-type (basic selection shown)
module ImmGen(
    input  [6:0] opcode,
    input  [31:0] instruction,
    output reg [31:0] immExt
);
    always @(*) begin
        case (opcode)
            7'b0010011, // I-type (addi, etc.)
            7'b0000011: // load (I-type)
                immExt = {{20{instruction[31]}}, instruction[31:20]};
            7'b0100011: // S-type (store)
                immExt = {{20{instruction[31]}}, instruction[31:25], instruction[11:7]};
            7'b1100011: // B-type (branch)
                immExt = {{19{instruction[31]}}, instruction[31], instruction[7], instruction[30:25], instruction[11:8], 1'b0};
            default:
                immExt = 32'b0;
        endcase
    end
endmodule

// Control unit (basic)
module control(
    input  [6:0] opcode,
    output reg Branch,
    output reg MemRead,
    output reg MemtoReg,
    output reg MemWrite,
    output reg ALUsrc,
    output reg RegWrite,
    output reg [1:0] ALUop
);
    always @(*) begin
        // defaults
        {Branch, MemRead, MemtoReg, MemWrite, ALUsrc, RegWrite, ALUop} = {1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,2'b00};
        case (opcode)
            7'b0110011: begin // R-type
                ALUsrc  = 1'b0;
                MemtoReg= 1'b0;
                RegWrite= 1'b1;
                MemRead = 1'b0;
                MemWrite= 1'b0;
                Branch  = 1'b0;
                ALUop   = 2'b10;
            end
            7'b0000011: begin // load (I-type)
                ALUsrc  = 1'b1;
                MemtoReg= 1'b1;
                RegWrite= 1'b1;
                MemRead = 1'b1;
                MemWrite= 1'b0;
                Branch  = 1'b0;
                ALUop   = 2'b00;
            end
            7'b0100011: begin // store (S-type)
                ALUsrc  = 1'b1;
                MemtoReg= 1'b0;
                RegWrite= 1'b0;
                MemRead = 1'b0;
                MemWrite= 1'b1;
                Branch  = 1'b0;
                ALUop   = 2'b00;
            end
            7'b1100011: begin // branch (B-type)
                ALUsrc  = 1'b0;
                MemtoReg= 1'b0;
                RegWrite= 1'b0;
                MemRead = 1'b0;
                MemWrite= 1'b0;
                Branch  = 1'b1;
                ALUop   = 2'b01;
            end
            default: begin
                // keep defaults
            end
        endcase
    end
endmodule

// ALU module
module ALU(
    input  [31:0] A,
    input  [31:0] B,
    input  [3:0] Control_in,
    output reg [31:0] res,
    output reg zero
);
    always @(*) begin
        case (Control_in)
            4'b0000: res = A & B; // AND
            4'b0001: res = A | B; // OR
            4'b0010: res = A + B; // ADD
            4'b0110: res = A - B; // SUB
            4'b0111: res = (A < B) ? 32'd1 : 32'd0; // SLT
            default: res = 32'd0;
        endcase
        zero = (res == 32'd0) ? 1'b1 : 1'b0;
    end
endmodule

// ALU control unit
module ALU_control(
    input  [1:0] ALUop,
    input        fun7,  // bit 30 of instruction typically
    input  [2:0] fun3,
    output reg [3:0] Control_out
);
    always @(*) begin
        // default
        Control_out = 4'b0010; // ADD
        case ({ALUop, fun7, fun3})
            6'b00_0_000: Control_out <= 4'b0010; // load/store -> ADD
            6'b01_0_000: Control_out <= 4'b0110; // branch -> SUB
            6'b10_0_000: Control_out <= 4'b0010; // R-type add
            6'b10_1_000: Control_out <= 4'b0110; // R-type sub (fun7=1)
            6'b10_0_111: Control_out <= 4'b0000; // AND
            6'b10_0_110: Control_out <= 4'b0001; // OR
            default: Control_out <= 4'b0010;
        endcase
    end
endmodule

// Data memory unit (word addressed)
module DataMem(
    input clk,
    input rst,
    input MemWrite,
    input MemRead,
    input [31:0] read_address,
    input [31:0] Write_data,
    output reg [31:0] MemData_out
);
    reg [31:0] Dmem [0:63];
    integer k;
    wire [5:0] idx;
    assign idx = read_address[7:2];

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            for (k = 0; k < 64; k = k + 1) begin
                Dmem[k] <= 32'b0;
            end
            MemData_out <= 32'b0;
        end
        else begin
            if (MemWrite) begin
                Dmem[idx] <= Write_data;
            end
            if (MemRead) begin
                MemData_out <= Dmem[idx];
            end
            else begin
                MemData_out <= 32'b0;
            end
        end
    end
endmodule

// Generic 2:1 MUX (32-bit)
module MUX2_32(
    input sel,
    input [31:0] A,
    input [31:0] B,
    output [31:0] Y
);
    assign Y = (sel == 1'b0) ? A : B;
endmodule

// AND logic for branch decision
module andLogic(
    input branch,
    input zero,
    output and_out
);
    assign and_out = branch & zero;
endmodule

// Adder (32-bit)
module Adder32(
    input [31:0] in1,
    input [31:0] in2,
    output [31:0] add_out
);
    assign add_out = in1 + in2;
endmodule

