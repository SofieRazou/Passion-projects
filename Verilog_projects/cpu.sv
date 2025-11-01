//====================== CPU ========================
module SimpleCPU(
    input clk,
    input reset
);
    reg [7:0] A, B, IR, PC;
    reg [7:0] memory [0:255];
    reg [3:0] opcode;
    reg [3:0] operand;

    always @(posedge clk) begin
        if (reset) begin
            PC <= 0;
        end else begin
            // Fetch
            IR <= memory[PC];
            PC <= PC + 1;

            // Decode
            opcode  <= IR[7:4];
            operand <= IR[3:0];

            // Execute
            case(opcode)
                4'b0001: A <= memory[operand];       // LOAD A
                4'b1001: B <= memory[operand];       // LOAD B
                4'b0010: A <= A + B;                 // ADD
                4'b0011: A <= A - B;                 // SUB
                4'b0110: memory[operand] <= A;       // STORE
                4'b0111: PC <= operand;              // JMP
            endcase
        end
    end
endmodule

