//====================== testbench ========================
`timescale 1ns/1ps

module cpu_tb;

    reg clk;
    reg reset;

    SimpleCPU uut (
        .clk(clk),
        .reset(reset)
    );

    // clock generator 10ns period
    always #5 clk = ~clk;

    initial begin
        $dumpfile("cpu.vcd");
        $dumpvars(0, cpu_tb);

        clk   = 0;
        reset = 1;

        // program preload
        uut.memory[0] = 8'b00010011; // LOAD A,3
        uut.memory[1] = 8'b10010100; // LOAD B,4
        uut.memory[2] = 8'b00100000; // ADD
        uut.memory[3] = 8'b01101010; // STORE A,10
        uut.memory[4] = 8'b01110100; // JMP 4
        
        // data preload
        uut.memory[3] = 5;
        uut.memory[4] = 7;

        #20;
        reset = 0;

        #200;

        $display("mem[10] = %0d (expected 12)", uut.memory[10]);

        $finish;
    end

endmodule
