import networkx as net
import matplotlib.pyplot as plt  
import numpy as np 

class TreeNode:
    def __init__(self, val, degree=0):
        self.val = val
        self.children = [None] * degree
     
    def add_edge(self, neighbor_node):
       
        for i in range(len(self.children)):
            if self.children[i] is None:
                self.children[i] = neighbor_node
                return True
        return False  

    def create_rec(self, degrees, nodes=None):
        if nodes is None:
            nodes = list(range(1, len(degrees) + 1))
       
        # Recursion basis 
        if len(nodes) == 2:
            if degrees[0] == 1 and degrees[1] == 1:
                return [(nodes[0], nodes[1])]
            else:
                raise ValueError("Impossible degree sequence!")
        

        di = next(i for i, d in enumerate(degrees) if d == 1)
        d = next(i for i, d in enumerate(degrees) if d > 1)

        edge = (nodes[di], nodes[d])

        degs = []
        new_nodes = []
        for i in range(len(degrees)):
            if i == di:
                continue 
            elif i == d:
                degs.append(degrees[i] - 1)
                new_nodes.append(nodes[i])
            else:
                
                degs.append(degrees[i])
                new_nodes.append(nodes[i])
      
        return [edge] + self.create_rec(degs, new_nodes)

    def visual(self, edges):
       #tree to graph for visuals 
        G = net.Graph()
        G.add_edges_from(edges)
        
      
        pos = net.spring_layout(G)
        net.draw(G, pos, with_labels=True, node_color='lightgreen', font_weight='bold', node_size=700)
        plt.show()

# --- Test main ---
if __name__ == "__main__":
    
    target_degrees = [1, 6, 2, 2, 1, 2, 1, 1, 1, 1]
    

    runner = TreeNode(val=0)
    
    # Compute  edge  matrix
    computed_edges = runner.create_rec(target_degrees)
    print("Generated Edges:", computed_edges)

    runner.visual(computed_edges)
