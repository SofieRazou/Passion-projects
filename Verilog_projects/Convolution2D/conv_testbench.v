`timescale 1ns/1ps

module tb_conv2d_fixed;

    parameter IMG_W = 128;
    parameter PIXEL_BITS = 8;

    reg clk = 0;
    reg rst_n = 0;
    reg [PIXEL_BITS-1:0] pixel_in = 0;
    reg pixel_valid = 0;

    wire [PIXEL_BITS-1:0] out_pixel;
    wire out_valid;

    // --- Instantiate your convolution module ---
    conv2d_3x3_fifo_full #(
        .IMG_W(IMG_W),
        .PIXEL_BITS(PIXEL_BITS)
    ) uut (
        .clk(clk),
        .rst_n(rst_n),
        .pixel_in(pixel_in),
        .pixel_valid(pixel_valid),
        .out_pixel(out_pixel),
        .out_valid(out_valid)
    );

    // --- Clock generation ---
    always #5 clk = ~clk; // 10ns period

    // --- File handles ---
    integer infile;
    integer outfile;
    integer status;
    integer pixel_val;

    initial begin
        // Open input file
        infile = $fopen("image_data.txt", "r");
        if (infile == 0) begin
            $display("ERROR: Could not open input file");
            $finish;
        end

        // Open output file
        outfile = $fopen("out_pixels.txt", "w");
        if (outfile == 0) begin
            $display("ERROR: Could not open output file");
            $finish;
        end

        // Reset
        rst_n = 0;
        pixel_valid = 0;
        #20;
        rst_n = 1;

        // Feed pixels
        while (!$feof(infile)) begin
            status = $fscanf(infile, "%d\n", pixel_val); // read pixel
            pixel_in = pixel_val[PIXEL_BITS-1:0];
            pixel_valid = 1;
            @(posedge clk);
        end

        pixel_valid = 0; // stop feeding pixels

        // Wait for last outputs
        repeat (IMG_W*3) @(posedge clk);

        // Close files
        $fclose(infile);
        $fclose(outfile);

        $display("Simulation finished!");
        $finish;
    end

    // Write output pixels to file
    always @(posedge clk) begin
        if (out_valid) begin
            $fwrite(outfile, "%d\n", out_pixel);
        end
    end

endmodule
