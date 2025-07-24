import matplotlib.pyplot as plt
import pandas as pd

data = pd.read_csv("data.txt")
data.columns = data.columns.str.strip()

plt.figure(figsize=(10,6))

data.columns = ["Azimuth", "Elevation"]
plt.plot(data["Azimuth"], label="Azimuth")
plt.plot(data["Elevation"], label="Elevation")

plt.xlabel("Time Step")
plt.ylabel("Degrees")
plt.title("Telescope positioning tracking trajectory")
plt.legend()
plt.grid(True)

plt.show()
