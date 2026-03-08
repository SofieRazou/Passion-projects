#include "sat_by_markov.hpp"

using namespace std;

// ---------------- Tree utilities ----------------

Node* clone(Node* root) {
    if (!root) return nullptr;
    return new Node(root->kind, root->val, clone(root->left), clone(root->right));
}

Node* eliminateImplications(Node* root) {
    if (root == nullptr)
        return nullptr;

    Node* left = eliminateImplications(root->left);
    Node* right = eliminateImplications(root->right);

    if (root->kind == "IMP") {
        Node* notA = new Node("NOT", 0, left, nullptr);
        return new Node("OR", 0, notA, right);
    }

    return new Node(root->kind, root->val, left, right);
}

Node* pushNegations(Node* root) {
    if (root == nullptr)
        return nullptr;

    if (root->kind == "VAR") {
        return new Node("VAR", root->val);
    }

    if (root->kind == "AND") {
        return new Node("AND", 0,
                        pushNegations(root->left),
                        pushNegations(root->right));
    }

    if (root->kind == "OR") {
        return new Node("OR", 0,
                        pushNegations(root->left),
                        pushNegations(root->right));
    }

    if (root->kind == "NOT") {
        Node* child = root->left;
        if (!child) return nullptr;

        if (child->kind == "VAR")
            return new Node("NOT", 0, new Node("VAR", child->val), nullptr);

        if (child->kind == "NOT")
            return pushNegations(child->left);

        if (child->kind == "AND") {
            Node* nl = new Node("NOT", 0, clone(child->left), nullptr);
            Node* nr = new Node("NOT", 0, clone(child->right), nullptr);
            return new Node("OR", 0, pushNegations(nl), pushNegations(nr));
        }

        if (child->kind == "OR") {
            Node* nl = new Node("NOT", 0, clone(child->left), nullptr);
            Node* nr = new Node("NOT", 0, clone(child->right), nullptr);
            return new Node("AND", 0, pushNegations(nl), pushNegations(nr));
        }
    }

    return nullptr;
}

Node* distributeOR(Node* a, Node* b) {
    if (!a || !b) return nullptr;

    if (a->kind == "AND") {
        return new Node("AND", 0,
                        distributeOR(a->left, clone(b)),
                        distributeOR(a->right, clone(b)));
    }

    if (b->kind == "AND") {
        return new Node("AND", 0,
                        distributeOR(clone(a), b->left),
                        distributeOR(clone(a), b->right));
    }

    return new Node("OR", 0, clone(a), clone(b));
}

Node* CNF(Node* root) {
    if (root == nullptr)
        return nullptr;

    if (root->kind == "VAR") {
        return new Node("VAR", root->val);
    }

    if (root->kind == "NOT") {
        return new Node("NOT", 0, clone(root->left), nullptr);
    }

    if (root->kind == "AND") {
        return new Node("AND", 0, CNF(root->left), CNF(root->right));
    }

    if (root->kind == "OR") {
        Node* l = CNF(root->left);
        Node* r = CNF(root->right);
        return distributeOR(l, r);
    }

    return nullptr;
}

// ---------------- MChain implementation ----------------

MChain::MChain(int maxSteps, double noiseProb)
    : numVariables(0), maxSteps(maxSteps), noise(noiseProb), bestEnergy(INT_MAX) {
    srand((unsigned)time(nullptr));
}

void MChain::setCNF(int numVars, const vector<vector<int>>& cnfClauses) {
    clauses = cnfClauses;
    numVariables = numVars;
}

bool MChain::solve() {
    assignment = randomAssignment();
    bestAssignment = assignment;
    bestEnergy = energy(assignment);

    for (int i = 0; i < maxSteps; ++i) {
        if (isSolution(assignment))
            return true;

        step();
        updateBest();
    }

    return false;
}

vector<int> MChain::getAssignment() const {
    return bestAssignment;
}

int MChain::getBestEnergy() const {
    return bestEnergy;
}

void MChain::step() {
    int clauseIdx = pickUnsatisfiedClause(assignment);
    if (clauseIdx == -1) return;

    int varIdx;
    double r = (double)rand() / RAND_MAX;

    if (r < noise) {
        const vector<int>& clause = clauses[clauseIdx];
        int lit = clause[rand() % clause.size()];
        varIdx = abs(lit) - 1;
    } else {
        varIdx = bestVariableInClause(clauseIdx, assignment);
    }

    if (varIdx != -1) {
        assignment[varIdx] ^= 1;
    }
}

void MChain::updateBest() {
    int e = energy(assignment);
    if (e < bestEnergy) {
        bestEnergy = e;
        bestAssignment = assignment;
    }
}