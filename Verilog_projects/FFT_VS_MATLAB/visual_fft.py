# from vcdvcd import VCDVCD

# vcd = VCDVCD("fft_tb.vcd")

# print("Signals found in VCD:")
# for s in vcd.signals:
#     print(s)

from vcdvcd import VCDVCD
import matplotlib.pyplot as plt

# Load VCD
vcd = VCDVCD("fft_tb.vcd", store_tvs=True)

# Detect X_R and X_I signals automatically
X_R_signals = sorted([sig for sig in vcd.signals if "X_R_flat" in sig])
X_I_signals = sorted([sig for sig in vcd.signals if "X_I_flat" in sig])

print("X_R signals found:", X_R_signals)
print("X_I signals found:", X_I_signals)

# Reconstruct the last value of each FFT output
X_r = [vcd[sig].tv[-1][1] for sig in X_R_signals]
X_i = [vcd[sig].tv[-1][1] for sig in X_I_signals]

# Print FFT output
print("\nFFT Output:")
for i in range(len(X_r)):
    print(f"X[{i}] = {X_r[i]} + j{X_i[i]}")

# Optional: plot real and imaginary parts
plt.figure(figsize=(10, 5))
plt.stem(range(len(X_r)), X_r, linefmt='b-', markerfmt='bo', basefmt='r-', label='Real')
plt.stem(range(len(X_i)), X_i, linefmt='g-', markerfmt='go', basefmt='r-', label='Imag')
plt.xlabel("FFT Bin")
plt.ylabel("Q1.31 Value")
plt.title("FFT Output")
plt.legend()
plt.grid(True)
plt.show()
