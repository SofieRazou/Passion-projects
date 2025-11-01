module SimpleGPU(
    input clk,
    input reset
);
    reg [7:0] Rcolor, Rx, Ry, IR, PC;
    reg [7:0] program [0:255];       // instruction memory
    reg [7:0] framebuffer [0:255];   // pixel memory
    reg [3:0] opcode;
    reg [3:0] operand;

    always @(posedge clk) begin
        if (reset) begin
            PC <= 0;
        end else begin
            IR <= program[PC];
            PC <= PC + 1;

            opcode <= IR[7:4];
            operand <= IR[3:0];

            case (opcode)
                4'b0001: Rcolor <= operand;                        // SET_COLOR
                4'b0010: Rx <= operand;                            // SET_X
                4'b0011: Ry <= operand;                            // SET_Y
                4'b0100: framebuffer[(Ry<<4) + Rx] <= Rcolor;     // DRAW pixel
                4'b0111: PC <= operand;                            // JMP
            endcase
        end
    end
endmodule
