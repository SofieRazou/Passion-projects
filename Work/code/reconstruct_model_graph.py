import sys
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx


GRAPH_FILE = Path(
    r"C:\Users\javot\Documents\MATLAB\Bern\simulink"
    r"\controller1_SR_graph.graphml"
)


def reconstruct_graph(filename: Path) -> nx.Graph:
    """Load and display a graph stored in GraphML format."""

    if not filename.exists():
        raise FileNotFoundError(f"GraphML file not found:\n{filename}")

    graph = nx.read_graphml(filename)

    print(f"Loaded graph with {graph.number_of_nodes()} nodes "
          f"and {graph.number_of_edges()} edges.")

    # A spring layout is suitable for general graphs.
    positions = nx.spring_layout(graph, seed=42)

    plt.figure(figsize=(14, 9))

    nx.draw_networkx(
        graph,
        pos=positions,
        with_labels=True,
        node_size=1800,
        font_size=8,
        arrows=graph.is_directed(),
        edge_color="gray",
    )

    plt.title("Converted Simulink Graph")
    plt.axis("off")
    plt.tight_layout()
    plt.show()

    return graph


def main() -> None:
    try:
        reconstruct_graph(GRAPH_FILE)
    except (FileNotFoundError, nx.NetworkXError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
