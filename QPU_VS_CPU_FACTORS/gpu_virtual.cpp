#include "gpu_virtual.hpp"
#include <iostream>
#include <cmath>
#include <numeric>
#include <random>
#include <unordered_map>
#include <omp.h>

using namespace std;

// ---------------------------
// QState constructor
// ---------------------------
QState::QState(int n) : amp(1 << n, 0) {}

// ---------------------------
// QGate constructor & methods
// ---------------------------
QGate::QGate(string n, vector<vector<Complex>> m) : name(n), matrix(m) {}

QGate QGate::H() {
    double sq = 1.0/sqrt(2);
    return QGate("H", {{sq,sq},{sq,-sq}});
}

void QGate::apply(QState &s, int qubit_index) {
    int N = s.amp.size();
    StateVector result = s.amp;

    #pragma omp parallel for
    for(int i = 0; i < N; ++i) {
        if(((i >> qubit_index) & 1) == 0) {
            int j = i | (1 << qubit_index);
            auto a = s.amp[i];
            auto b = s.amp[j];
            result[i] = matrix[0][0]*a + matrix[0][1]*b;
            result[j] = matrix[1][0]*a + matrix[1][1]*b;
        }
    }
    s.amp = result;
}

// ---------------------------
// Modular exponentiation
// ---------------------------
long long modexp(long long a, long long e, long long N) {
    long long r = 1;
    a %= N;
    while (e > 0) {
        if (e & 1) r = (r * a) % N;
        a = (a * a) % N;
        e >>= 1;
    }
    return r;
}

// ---------------------------
// Continued fraction
// ---------------------------
long long continued_fraction(long long m, long long Q, long long N) {
    long double x = (long double)m / Q;
    long long a0 = floor(x);
    long long p0 = 1, q0 = 0;
    long long p1 = a0, q1 = 1;
    long double frac = x - a0;

    while (q1 < N) {
        if (fabsl(frac) < 1e-12) break;
        frac = 1.0L / frac;
        long long a = floor(frac);
        frac -= a;
        long long p2 = a * p1 + p0;
        long long q2 = a * q1 + q0;
        p0 = p1; q0 = q1;
        p1 = p2; q1 = q2;
    }
    return q1;
}

// ---------------------------
// Quantum Fourier Transform
// ---------------------------
void QFT(QState &s) {
    int N = s.amp.size();
    StateVector result(N);

    #pragma omp parallel for
    for(int k = 0; k < N; ++k) {
        Complex sum = 0;
        for(int j = 0; j < N; ++j) {
            double angle = 2.0 * M_PI * j * k / N;
            sum += s.amp[j] * polar(1.0, angle);
        }
        result[k] = sum / sqrt(N);
    }
    s.amp = result;
}

// ---------------------------
// Simulated quantum period finding
// ---------------------------
int quantum_period_finding(int a, int N) {
    int n = ceil(log2(N));
    int Q = 1 << (2*n);
    QState psi(2*n);
    double amp = 1.0 / sqrt(Q);
    for(auto &x : psi.amp) x = amp;

    unordered_map<long long, vector<int>> buckets;
    for(int x = 0; x < Q; ++x)
        buckets[modexp(a, x, N)].push_back(x);

    auto it = next(buckets.begin(), rand() % buckets.size());
    QState collapsed(2*n);
    double norm_factor = 1.0 / sqrt(it->second.size());
    for(int x : it->second) collapsed.amp[x] = norm_factor;

    psi.amp.swap(collapsed.amp);

    QFT(psi);

    vector<double> probs(Q);
    for(int i = 0; i < Q; ++i) probs[i] = norm(psi.amp[i]);
    mt19937 gen(random_device{}());
    discrete_distribution<int> dist(probs.begin(), probs.end());
    int m = dist(gen);

    return continued_fraction(m, Q, N);
}

// ---------------------------
// Shor's algorithm
// ---------------------------
int Shors(int N) {
    if(N % 2 == 0) return 2;

    mt19937 gen(random_device{}());
    uniform_int_distribution<int> dis(2, N-1);

    while(true) {
        int a = dis(gen);
        int g = gcd(a,N);
        if(g != 1) return g;

        int r = quantum_period_finding(a, N);
        if(r <= 0 || (r & 1)) continue;

        long long x = modexp(a, r/2, N);
        if(x == N-1) continue;

        int f1 = gcd(x+1,N);
        int f2 = gcd(x-1,N);

        if(f1 != 1 && f1 != N) return f1;
        if(f2 != 1 && f2 != N) return f2;
    }
}

// ---------------------------
// Main
// ---------------------------
// int main() {
//     int N = 33;
//     int trials = 3;
//     vector<double> timings;

//     cout << "Simulated Shor's algorithm for N=" << N << endl;

//     for(int t=0; t<trials; ++t){
//         auto start = chrono::high_resolution_clock::now();
//         int factor = Shors(N);
//         auto end = chrono::high_resolution_clock::now();
//         double elapsed = chrono::duration<double>(end-start).count();
//         timings.push_back(elapsed);
//         cout << "Trial " << t+1 << ": factor found = " << factor
//              << " (elapsed = " << elapsed << " s)" << endl;
//     }

//     double avg_time = accumulate(timings.begin(), timings.end(), 0.0) / timings.size();
//     cout << "\nAverage runtime: " << avg_time << " s" << endl;

//     return 0;
// }