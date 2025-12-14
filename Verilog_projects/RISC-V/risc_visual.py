# from vcdvcd import VCDVCD

# vcd = VCDVCD("test_tb.vcd")

# print("Signals found in VCD:")
# for s in vcd.signals:
#     print(s)

import matplotlib
matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
from vcdvcd import VCDVCD

# Load VCD
vcd = VCDVCD("test_tb.vcd", store_tvs=True)

# Correct signal paths (from your VCD output)
signal_paths = {
    "PC_out": "tb_top.PC_out[31:0]",
    "instruction_out": "tb_top.instruction_out[31:0]",
    "rd1_out": "tb_top.rd1_out[31:0]",
    "rd2_out": "tb_top.rd2_out[31:0]",
    "alu_result_out": "tb_top.alu_result_out[31:0]",
    "MemData_out_out": "tb_top.MemData_out_out[31:0]",
}

plt.figure(figsize=(12, 8))

for label, path in signal_paths.items():
    tv = vcd[path].tv
    times = [t for t, v in tv]
    values = [int(v, 2) for t, v in tv]  # vectors → int
    plt.step(times, values, where="post", label=label)

plt.xlabel("Time (ns)")
plt.ylabel("Value")
plt.title("CPU Signals Over Time")
plt.legend()
plt.grid(True)
plt.show()
