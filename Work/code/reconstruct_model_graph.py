import networkx as nx
import sys
GRAPH_FILE = "C::/Users/javot/Documents/MATLAB/Bern/simulink/controller1_SR_graph.graphml"

def reconstruct_graph(filename):
    graph = nx.read_graphml(filename)
    nx.draw(graph)

def main():
    reconstruct_graph(GRAPH_FILE)

if __name__ =="main":
    main()