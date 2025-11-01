//==================== QPU 1-Qubit Module ====================
module QPU_1qubit(
    input clk,
    input reset,
    input [1:0] gate,
    output real qubit0,
    output real qubit1
);
    real q0, q1;
    real temp0, temp1; // temporary variables for gates

    assign qubit0 = q0;
    assign qubit1 = q1;

    always @(posedge clk) begin
        if (reset) begin
            q0 = 1.0;
            q1 = 0.0;
        end else begin
            case(gate)
                2'b01: begin // X gate
                    temp0 = q0;
                    q0 = q1;
                    q1 = temp0;
                end
                2'b10: begin // Hadamard gate
                    temp0 = (q0 + q1)/1.4142;
                    temp1 = (q0 - q1)/1.4142;
                    q0 = temp0;
                    q1 = temp1;
                end
                default: begin
                    // do nothing (identity)
                end
            endcase
        end
    end
endmodule
