# from vcdvcd import VCDVCD

# vcd = VCDVCD("trigos_tb.vcd")

# print("Signals found in VCD:")
# for s in vcd.signals:
#     print(s)

import matplotlib.pyplot as plt
from vcdvcd import VCDVCD

# Load VCD
vcd = VCDVCD("trigos_tb.vcd", store_tvs=True)

# Use the exact signal names from your VCD
cos_signal = vcd['trigos_tb.uut.cos_out[31:0]']
sin_signal = vcd['trigos_tb.uut.sin_out[31:0]']

# Extract times and values
times = [tv[0] for tv in cos_signal.tv]
cos_values = [tv[1] for tv in cos_signal.tv]
sin_values = [tv[1] for tv in sin_signal.tv]

# Plot
plt.figure(figsize=(12,6))
plt.step(times, cos_values, where='post', label='cos_out')
plt.step(times, sin_values, where='post', label='sin_out')
plt.xlabel("Time (ns)")
plt.ylabel("Value (Q1.31)")
plt.title("CORDIC Cos/Sin Outputs")
plt.legend()
plt.grid(True)
plt.show()
