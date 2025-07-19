import pandas as pd
import matplotlib.pyplot as plt

# Load and clean CSV
data = pd.read_csv("game_results.txt")
data.columns = data.columns.str.strip()

# Count wins
counts = data['Winner'].value_counts()
print(f"Alice's wins: {counts.get('Alice', 0)}")
print(f"Bob's wins: {counts.get('Bob', 0)}")

# Plot
counts = counts.reindex(['Alice', 'Bob']).fillna(0)
counts.plot(kind='bar', color=['green', 'blue'])
plt.title('Monte Carlo vs Greedy Wins')
plt.ylabel('Number of Wins')
plt.xlabel('Player')
plt.grid(axis='y', linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig('game_wins_plot.png')
plt.show()
