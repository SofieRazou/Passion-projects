#include <iostream>
#include <iomanip>
#include <cmath>
#include <queue>
#include <complex>
#include <vector>
#include <fstream>

using namespace std;
using Complex = complex<double>;  // Alias for complex numbers

// ---------------- Classical Graph Representation ----------------
class Graph {
private:
    int n;
    vector<vector<int>> adj;

public:
    Graph(int N) : n(N), adj(N) {}

    int size() const { return n; }

    void addEdge(int u, int v) {
        adj[u].push_back(v);
        adj[v].push_back(u); // undirected
    }

    int BFS(int start, int target) {
        vector<bool> visited(n, false);
        queue<pair<int,int>> q;
        q.push({start,0});
        visited[start] = true;

        while(!q.empty()) {
            auto [u, steps] = q.front(); q.pop();
            if(u == target) return steps;
            for(int v : adj[u]){
                if(!visited[v]){
                    visited[v] = true;
                    q.push({v, steps+1});
                }
            }
        }
        return -1;
    }

    // Public method to safely get all edges
    vector<pair<int,int>> getEdges() const {
        vector<pair<int,int>> edges;
        vector<vector<bool>> written(n, vector<bool>(n,false));
        for(int u=0; u<n; ++u){
            for(int v : adj[u]){
                if(!written[u][v]){
                    edges.push_back({u,v});
                    written[u][v] = written[v][u] = true;
                }
            }
        }
        return edges;
    }

    friend struct QuantumWalk;
};

// ---------------- Quantum Walk Implementation -----------------
struct QuantumWalk {
    int n;
    vector<vector<double>> L;  // Laplacian
    vector<Complex> state;

    QuantumWalk(const Graph &g) {
        n = g.size();
        L.resize(n, vector<double>(n, 0.0));
        for(int i=0;i<n;++i){
            int deg = g.adj[i].size();
            L[i][i] = deg;
            for(int j : g.adj[i]) L[i][j] = -1.0;
        }
        double norm = 1.0/sqrt(n);
        state.resize(n, Complex(norm,0));
    }

    void step(double gamma, double dt){
        vector<Complex> new_state(n, Complex(0,0));
        for(int i=0;i<n;++i){
            Complex sum(0,0);
            for(int j=0;j<n;++j) sum += state[j]*L[i][j];
            new_state[i] = state[i] - Complex(0,1)*gamma*dt*sum;
        }
        state = new_state;
    }

    void oracle(int target){
        if(target>=0 && target<n) state[target] *= -1.0;
    }

    vector<double> probs() const {
        vector<double> prob(n,0.0);
        for(int i=0;i<n;++i) prob[i] = norm(state[i]);
        return prob;
    }

    vector<vector<double>> quantum_len(int start, int target, int steps, double dt, double gamma){
        vector<vector<double>> probHistory;
        for(int t=0;t<steps;++t){
            if(target != -1) oracle(target);
            step(gamma, dt);
            probHistory.push_back(probs());
        }
        return probHistory;
    }
};

// ---------------- Test Main -----------------------------------
int main(){
    // Create graph
    Graph g(6);
    g.addEdge(0,1);
    g.addEdge(0,2);
    g.addEdge(1,3);
    g.addEdge(2,3);
    g.addEdge(3,4);
    g.addEdge(4,5);

    int start = 0;
    int target = 3;
    double dt = 0.1;
    double gamma = 1.0;
    int steps = 5;

    // Quantum Walk
    QuantumWalk q(g);
    auto history = q.quantum_len(start,target,steps,dt,gamma);

    // --- 1. Write nodes.txt ---
    ofstream nodes_file("nodes.txt");
    if(!nodes_file.is_open()){ cerr << "Error opening nodes.txt!\n"; return 1; }

    for(int t=0;t<steps;++t){
        auto probs = history[t];
        double maxProb = 0.0;
        int maxNode = -1;
        for(int i=0;i<probs.size();++i){
            if(probs[i] > maxProb){
                maxProb = probs[i];
                maxNode = i;
            }
        }

        cout << "Step " << t+1 << ": Node " << maxNode
             << " with probability " << fixed << setprecision(3) << maxProb << endl;

        nodes_file << t+1 << " " << maxNode << " " << fixed << setprecision(6) << maxProb << "\n";
    }
    nodes_file.close();

    // --- 2. Write edges.txt ---
    ofstream edges_file("edges.txt");
    if(!edges_file.is_open()){ cerr << "Error opening edges.txt!\n"; return 1; }

    auto edges = g.getEdges();
    for(auto &e : edges){
        edges_file << e.first << " " << e.second << "\n";
    }
    edges_file.close();

    return 0;
}
