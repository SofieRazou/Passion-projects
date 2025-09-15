import networkx as nx
import matplotlib.pyplot as plt

# Read edges from edges.txt
G = nx.Graph()
with open("edges.txt", "r") as f:
    for line in f:
        u, v = map(int, line.strip().split())
        G.add_edge(u, v)

# Compute BFS path
start = 0
target = 3
bfs_path = nx.shortest_path(G, source=start, target=target)

# Read quantum walk max nodes from nodes.txt
qw_path = []
with open("nodes.txt", "r") as f:
    for line in f:
        _, node, _ = line.strip().split()
        qw_path.append(int(node))

# Draw graph
pos = nx.spring_layout(G, seed=42)  # fixed layout

plt.figure(figsize=(8,6))

# Draw all nodes and edges
nx.draw(G, pos, with_labels=True, node_color='lightgray', edge_color='gray', node_size=600)

# Highlight BFS path in blue
nx.draw_networkx_nodes(G, pos, nodelist=bfs_path, node_color='blue')
nx.draw_networkx_edges(G, pos, edgelist=list(zip(bfs_path[:-1], bfs_path[1:])), width=3, edge_color='blue', label='BFS path')

# Highlight Quantum Walk path in red
nx.draw_networkx_nodes(G, pos, nodelist=qw_path, node_color='red')
nx.draw_networkx_edges(G, pos, edgelist=list(zip(qw_path[:-1], qw_path[1:])), width=3, edge_color='red', style='dashed', label='Quantum Walk')

plt.title("BFS (blue) vs Quantum Walk (red) Paths")
plt.legend()
plt.axis('off')
plt.show()
