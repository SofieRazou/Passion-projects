#ifndef SAT_BY_MARKOV_HPP
#define SAT_BY_MARKOV_HPP

#include <iostream>
#include <vector>
#include <string>
#include <cstdlib>
#include <ctime>
#include <climits>

using namespace std;

struct Node {
    string kind;
    int val;
    Node* left;
    Node* right;

    Node(string k, int v = 0, Node* l = nullptr, Node* r = nullptr)
        : kind(k), val(v), left(l), right(r) {}

    string print_tree() const {
        if (kind == "VAR") {
            return "x" + to_string(val);
        }

        if (kind == "NOT") {
            if (!left) return "";
            return "(!" + left->print_tree() + ")";
        }

        if (kind == "AND") {
            string L = left ? left->print_tree() : "";
            string R = right ? right->print_tree() : "";
            return "(" + L + " AND " + R + ")";
        }

        if (kind == "OR") {
            string L = left ? left->print_tree() : "";
            string R = right ? right->print_tree() : "";
            return "(" + L + " OR " + R + ")";
        }

        if (kind == "IMP") {
            string L = left ? left->print_tree() : "";
            string R = right ? right->print_tree() : "";
            return "(" + L + " -> " + R + ")";
        }

        if (kind == "IFF") {
            string L = left ? left->print_tree() : "";
            string R = right ? right->print_tree() : "";
            return "(" + L + " <-> " + R + ")";
        }

        return "";
    }

    friend ostream& operator<<(ostream& os, const Node& n) {
        os << n.print_tree();
        return os;
    }
};

// Function declarations only
Node* clone(Node* root);
Node* eliminateImplications(Node* root);
Node* pushNegations(Node* root);
Node* distributeOR(Node* a, Node* b);
Node* CNF(Node* root);

class MChain {
public:
    MChain(int maxSteps, double noiseProb);

    void setCNF(int numVars, const vector<vector<int>>& cnfClauses);

    bool solve();
    vector<int> getAssignment() const;
    int getBestEnergy() const;

private:
    int numVariables;
    int maxSteps;
    double noise;

    vector<vector<int>> clauses;

    vector<int> assignment;
    vector<int> bestAssignment;
    int bestEnergy;

    vector<int> randomAssignment() {
        vector<int> a(numVariables);
        for (int i = 0; i < numVariables; ++i) a[i] = rand() % 2;
        return a;
    }

    bool clauseSatisfied(const vector<int>& clause, const vector<int>& assign) const {
        for (int literal : clause) {
            int idx = abs(literal) - 1;
            if (literal > 0 && assign[idx] == 1) return true;
            if (literal < 0 && assign[idx] == 0) return true;
        }
        return false;
    }

    vector<int> unsatisfiedClauseIndices(const vector<int>& assign) const {
        vector<int> unsat;
        for (int i = 0; i < (int)clauses.size(); ++i) {
            if (!clauseSatisfied(clauses[i], assign)) unsat.push_back(i);
        }
        return unsat;
    }

    int energy(const vector<int>& assign) const {
        return (int)unsatisfiedClauseIndices(assign).size();
    }

    bool isSolution(const vector<int>& assign) const {
        return energy(assign) == 0;
    }

    vector<int> flipVariable(const vector<int>& assign, int varIndex) const {
        vector<int> flipped = assign;
        flipped[varIndex] ^= 1;
        return flipped;
    }

    int pickUnsatisfiedClause(const vector<int>& assign) const {
        vector<int> unsat = unsatisfiedClauseIndices(assign);
        if (unsat.empty()) return -1;
        return unsat[rand() % unsat.size()];
    }

    int bestVariableInClause(int clauseIndex, const vector<int>& assign) const {
        int bestVar = -1;
        int bestE = INT_MAX;

        for (int literal : clauses[clauseIndex]) {
            int varIdx = abs(literal) - 1;
            vector<int> can = flipVariable(assign, varIdx);
            int e = energy(can);
            if (e < bestE) {
                bestE = e;
                bestVar = varIdx;
            }
        }
        return bestVar;
    }

    void step();
    void updateBest();
};

#endif