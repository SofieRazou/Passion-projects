// #include<pybind11/pybind11.h>
#include <iostream>
#include <vector>
#include "sat_by_markov.hpp"
using namespace std;

int main() {
    // (x1 AND !x1) AND (x2 AND !x2) AND ... AND (x8 AND !x8)

    Node* formula = new Node(
        "AND", 0,

        new Node(
            "AND", 0,

            new Node(
                "AND", 0,

                new Node(
                    "AND", 0,

                    new Node(
                        "AND", 0,

                        new Node(
                            "AND", 0,

                            new Node(
                                "AND", 0,

                                new Node(
                                    "AND", 0,

                                    new Node("VAR", 1),
                                    new Node("NOT", 0, new Node("VAR", 1), nullptr)
                                ),

                                new Node(
                                    "AND", 0,
                                    new Node("VAR", 2),
                                    new Node("NOT", 0, new Node("VAR", 2), nullptr)
                                )
                            ),

                            new Node(
                                "AND", 0,
                                new Node("VAR", 3),
                                new Node("NOT", 0, new Node("VAR", 3), nullptr)
                            )
                        ),

                        new Node(
                            "AND", 0,
                            new Node("VAR", 4),
                            new Node("NOT", 0, new Node("VAR", 4), nullptr)
                        )
                    ),

                    new Node(
                        "AND", 0,
                        new Node("VAR", 5),
                        new Node("NOT", 0, new Node("VAR", 5), nullptr)
                    )
                ),

                new Node(
                    "AND", 0,
                    new Node("VAR", 6),
                    new Node("NOT", 0, new Node("VAR", 6), nullptr)
                )
            ),

            new Node(
                "AND", 0,
                new Node("VAR", 7),
                new Node("NOT", 0, new Node("VAR", 7), nullptr)
            )
        ),

        new Node(
            "AND", 0,
            new Node("VAR", 8),
            new Node("NOT", 0, new Node("VAR", 8), nullptr)
        )
    );

    cout << "Original formula:\n" << *formula << "\n\n";

    Node* noImp = eliminateImplications(formula);
    cout << "After eliminating implications:\n";
    if (noImp) cout << *noImp << "\n\n";
    else cout << "nullptr\n\n";

    Node* nnf = pushNegations(noImp);
    cout << "After pushing negations:\n";
    if (nnf) cout << *nnf << "\n\n";
    else cout << "nullptr\n\n";

    Node* cnfTree = CNF(nnf);
    cout << "CNF tree:\n";
    if (cnfTree) cout << *cnfTree << "\n\n";
    else cout << "nullptr\n\n";

    // Equivalent CNF clauses:
    // (x1) AND (!x1) AND ... AND (x8) AND (!x8)
    vector<vector<int>> clauses = {
        { 1}, {-1},
        { 2}, {-2},
        { 3}, {-3},
        { 4}, {-4},
        { 5}, {-5},
        { 6}, {-6},
        { 7}, {-7},
        { 8}, {-8}
    };

    MChain solver(50000, 0.30);
    solver.setCNF(8, clauses);

    bool solved = solver.solve();

    if (solved) {
        cout << "Solution found.\n";
    } else {
        cout << "No exact solution found within max steps.\n";
        cout << "This is expected, because the formula is UNSAT.\n";
    }

    vector<int> ans = solver.getAssignment();

    cout << "\nBest assignment found:\n";
    for (int i = 0; i < (int)ans.size(); ++i) {
        cout << "x" << i + 1 << " = " << ans[i] << "\n";
    }

    cout << "\nBest energy = " << solver.getBestEnergy() << "\n";
    cout << "(For this formula, best energy cannot be 0.)\n";

    return 0;
}