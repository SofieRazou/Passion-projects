#pragma once
#include <vector>
#include <complex>
#include <string>

using Complex = std::complex<double>;
using StateVector = std::vector<Complex>;

// ---------------------------
// QState
// ---------------------------
struct QState {
    StateVector amp; // amplitudes
    QState(int n);   // constructor
};

// ---------------------------
// QGate
// ---------------------------
class QGate {
public:
    std::string name;
    std::vector<std::vector<Complex>> matrix;

    QGate(std::string n, std::vector<std::vector<Complex>> m);

    static QGate H();
    void apply(QState &s, int qubit_index);
};

// ---------------------------
// Modular exponentiation
// ---------------------------
long long modexp(long long a, long long e, long long N);

// ---------------------------
// Continued fraction
// ---------------------------
long long continued_fraction(long long m, long long Q, long long N);

// ---------------------------
// Quantum Fourier Transform
// ---------------------------
void QFT(QState &s);

// ---------------------------
// Simulated quantum period finding
// ---------------------------
int quantum_period_finding(int a, int N);

// ---------------------------
// Shor's algorithm
// ---------------------------
int Shors(int N);