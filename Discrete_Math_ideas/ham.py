import networkx as nx
import matplotlib.pyplot as plt

# PARAMETERS
k = 20
n = 2 * k

G = nx.Graph()
G.add_nodes_from(range(1, n+1))


def across(x):
    if x == 1:
        return k
    elif 2 <= x <= k - 1:
        return x + k + 1
    else:
        raise ValueError(f"No across edge from {x}")
    
def across(x):
    if x == 1:
        return k
    elif x == k:
        return 1
    elif 2 <= x <= k - 1:
        return x + k + 1
    elif k + 3 <= x <= 2*k: 
        return x - (k + 1)
    else:
        raise ValueError(f"No across edge from {x}")



def bridge(x):
    if x == k-2:
        return k+1
    elif x == k-1:
        return k+2
    if x == k+1:
        return k-2
    elif x == k+2:
        return k-1
    else: 
        raise ValueError("There aint no bridge here homie\n")
# -------------------------------------------------
# Build graph
# -------------------------------------------------

# Chord 1 -> k
G.add_edge(1, k)

# Chords i -> i+k+1
for i in range(2, k):
    G.add_edge(i, across(i))

# Peripheral edges except (k-2, k-1)
for i in range(1, n):
    if i != k - 2:
        G.add_edge(i, i + 1)

G.add_edge(n, 1)

# Special chords
G.add_edge(k - 1, k + 2)
G.add_edge(k - 2, k + 1)


# -------------------------------------------------
# Repair cycle
# -------------------------------------------------

def repair(u, v):
    u, v = sorted((u, v))
    circle = []

    # Case 1: (2, 5) deleted
    if (u, v) == (k - 2, k + 1):
        circle.append(k-2)
        circle.append(across(k-2))
        # FIXED: range(6, 2, -1) yields 6, 5, 4, 3
        for i in range(across(k-2)-1, k-2, -1):
            circle.append(i)
        circle.append(across(k-1))
        # FIXED: range(1, 2) yields 1
        for i in range(1, k-2):
            circle.append(i)
        circle.append(k-2)  # Complete the cycle
        
    # Case 2: (3, 6) deleted
    elif (u, v) == (k - 1, k + 2):
        circle.append(k-1)
        circle.append(across(k-1))
        # FIXED: range(7, 3, -1) yields 7, 6, 5, 4
        for i in range(across(k-1)-1, k-1, -1):
            circle.append(i)
        # FIXED: range(1, 3) yields 1, 2
        for i in range(1, k-1):
            circle.append(i)
        circle.append(k-1)  # Complete the cycle

    # SOLVED!!
    elif (u, v) == (k + 2, k + 3):
        circle.append(k+2)
        circle.append(bridge(k+2))
        circle.append(k)
        circle.append(1)
        for i in range(2*k, k+2, -1):
            circle.append(i)
        start_left = (across(k+3) + 1) if k+2 <= k-1 else 2
        for i in range(start_left, k - 1):
            circle.append(i)
        circle.append(bridge(k-2))
        circle.append(k+2)


    #SOLVED!!
    elif (u, v) == (k + 1, k + 2):
        circle.append(k+1)
        circle.append(bridge(k+1))
        for i in range(k-3, 0, -1):
            circle.append(i)
        for i in range(2*k, k+1, -1):
            circle.append(i)
        circle.append(bridge(k+2))
        circle.append(k)
        circle.append(k+1)

    # Case 5: (4, 5) deleted
    elif (u, v) == (k, k + 1):
        circle.append(k)
        circle.append(1)
        # FIXED: range(8, 6, -1) yields 8, 7
        for i in range(2*k, k+2, -1):
            circle.append(i)
        circle.append(across(k+3))
        # FIXED: range(2, 2) is empty
        for i in range(across(k+3)+1, k-2):
            circle.append(i)
        # FIXED: range(5, 5) is empty
        for i in range(bridge(k-2), k + 1):
            circle.append(i)
        circle.append(k)  # Complete the cycle

    # Case 6: Chord (2, 7) deleted
    elif 2 <= u <= k - 1 and v == across(u):
        circle.append(v)
        # FIXED: range(8, 9) yields 8
        for i in range(v+1, 2*k+1):
            circle.append(i)
        # FIXED: range(1, 3) yields 1, 2
        for i in range(1, k-1):
            circle.append(i)
        circle.append(bridge(k-2))
        circle.append(k)
        circle.append(k-1)
        # FIXED: range(6, 7) yields 6
        for i in range(k+2, v):
            circle.append(i)
        circle.append(v)  # Complete the cycle

    # Problem
    elif (v == u+1 and ((1<u and u<=k-2))):
        circle.append(v)
        circle.append(across(v))
        # FIXED: Includes node 2*k
        for i in range(across(v)+1, 2*k+1):
            circle.append(i)
        
        for i in range(1, u+1):
            circle.append(i)
        circle.append(across(u))
        for i in range(across(u)-1, k+1, -1):
            circle.append(i)
        circle.append(bridge(k+2))
        circle.append(k)
        circle.append(k+1)
        circle.append(bridge(k+1))
        for i in range(bridge(k+1)-1, v-1, -1):
            circle.append(i)

    elif (v == u+1 and (u >= k+3)):
        circle.append(u)
        circle.append(across(u))
        for i in range(across(u)-1, 0, -1):
            circle.append(i)
        for i in range(2*k, v-1, -1):
            circle.append(i)
        circle.append(across(v))
        
        # FIXED: If across(v) lands exactly on k-1, follow the outer perimeter directly
        if across(v) == k - 1:
            # Sequentially clear the remaining right perimeter nodes up to u
            for i in range(k, u):
                circle.append(i)
        else:
            # Standard structural track for inner right-side cuts (like 12, 13)
            for i in range(across(v)+1, k-1):
                circle.append(i)
            circle.append(bridge(k-2))
            circle.append(k)
            circle.append(k-1)
            circle.append(bridge(k-1))
            for i in range(bridge(k-1)+1, u):
                circle.append(i)
                
        circle.append(u)  # Cleanly closes the cycle back to the origin


    elif (u,v) == (1,2*k):
        for i in range(1, k-1):
            circle.append(i)
        circle.append(k+1)
        for i in range(k+2,2*k+1):
            circle.append(i)
        circle.append(k-1)
        circle.append(k)
        circle.append(1)
    
    elif (u, v) == (1, 2):
        circle.append(1)
        circle.append(k)
        circle.append(k-1)
        circle.append(bridge(k-1))  # Goes to k+2
        circle.append(k+1)
        circle.append(bridge(k+1))  # FIXED: Changed from across to bridge to get k-2

        # FIXED: Loop now starts correctly at (k-2)-1 and counts backward down to 2
        for i in range(bridge(k+1)-1, 1, -1):
            circle.append(i)

        for i in range(k+3, 2*k+1):
            circle.append(i)
        circle.append(1)

    
    elif ((u, v) == (k - 1, k) and (k-2<u<k+3)):
        circle.append(1)
        # 1. Move clockwise up the left side to k-2 (inclusive -> b+1 = k-1)
        for i in range(2, k - 1):
            circle.append(i)
            
        # 2. Use the lower bridge chord to jump across to the right side (node 9)
        circle.append(bridge(k - 2))
        
        # 3. Step clockwise up to k+2 (node 10)
        circle.append(k + 2)
        
        # 4. Use the upper bridge chord to jump back to the left side (node 7)
        circle.append(bridge(k + 2))
        
        # 5. Move to node k (node 8)
        circle.append(k)
        
        # 6. Complete the entire remaining upper right perimeter clockwise up to 2*k
        # (inclusive -> b+1 = 2*k+1)
        for i in range(k + 3, 2 * k + 1):
            circle.append(i)
            
        circle.append(1)  # Cleanly completes the cycle back to the origin

    elif (u,v)==(1,k):
        for i in range(1, k-1):
            circle.append(i)
        circle.append(k+1)
        circle.append(k)
        circle.append(k-1)
        for i in range(bridge(k-1), 2*k+1):
            circle.append(i)

        circle.append(1)

    else:
        raise ValueError(f"No repair rule for edge ({u},{v})")

    return circle

# -------------------------------------------------
# Draw graph
# -------------------------------------------------

def draw_graph(ham_cycle=None, removed_edge=None):

    pos = nx.circular_layout(G)

    plt.figure(figsize=(9, 9))

    nx.draw_networkx_nodes(
        G,
        pos,
        node_color="lightblue",
        node_size=700
    )

    nx.draw_networkx_labels(
        G,
        pos,
        font_weight="bold"
    )

    nx.draw_networkx_edges(
        G,
        pos,
        edge_color="lightgray",
        width=2
    )

    # deleted edge
    if removed_edge is not None:

        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=[removed_edge],
            edge_color="red",
            width=4,
            style="dashed"
        )

    # Hamiltonian cycle
    if ham_cycle is not None:

        E = list(zip(ham_cycle[:-1], ham_cycle[1:]))

        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=E,
            edge_color="limegreen",
            width=4
        )

    plt.title(f"Hamiltonian Repair Graph (k={k})")
    plt.axis("off")
    plt.show()
# -------------------------------------------------
# Main
# -------------------------------------------------

def main():
    draw_graph()

    u = int(input("Give u: "))
    v = int(input("Give v: "))

    if G.has_edge(u, v):
        G.remove_edge(u, v)
    else:
        print("Warning: this edge is not in G.")

    ham = repair(u, v)

    print("Hamiltonian repair cycle:")
    print(" -> ".join(map(str, ham)))

    print(f"Length: {len(ham)}")
    print(f"Unique vertices: {len(set(ham[:-1]))}")

    if ham[0] == ham[-1] and len(set(ham[:-1])) == n:
        print("Valid Hamiltonian cycle.")
    else:
        print("Problem with the cycle.")


if __name__ == "__main__":
    main()
