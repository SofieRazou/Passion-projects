#include <iostream>
#include <vector>
#include <complex>
#include <cmath>
#include <bitset>
#include "serial/serial.h"   

using namespace std;
using Complex = complex<double>;

// ---------------------- QMatrix Class ----------------------
class QMatrix {
private:
    int nrow, ncol;
    vector<vector<Complex>> values;

public:
    QMatrix(int rows, int columns)
        : nrow(rows), ncol(columns), values(rows, vector<Complex>(columns, 0)) {}

    int nrows() const { return nrow; }
    int ncols() const { return ncol; }

    Complex& operator()(int row, int col) { return values[row][col]; }
    const Complex& operator()(int row, int col) const { return values[row][col]; }

    vector<Complex> getRow(int row) const { return values[row]; }

    // Kronecker product
    QMatrix operator*(const QMatrix &q) const {
        QMatrix res(nrow*q.nrows(), ncol*q.ncols());
        for(int i = 0; i < nrow; ++i)
            for(int j = 0; j < ncol; ++j)
                for(int k = 0; k < q.nrows(); ++k)
                    for(int l = 0; l < q.ncols(); ++l)
                        res(i*q.nrows()+k, j*q.ncols()+l) = values[i][j] * q(k,l);
        return res;
    }

    // Multiply matrix by state vector
    vector<Complex> multiply(const vector<Complex> &state) const {
        vector<Complex> result(nrow, 0);
        for(int i = 0; i < nrow; ++i)
            for(int j = 0; j < ncol; ++j)
                result[i] += values[i][j] * state[j];
        return result;
    }
};

// ---------------------- Fundamental Quantum Gates ----------------------
namespace Gates {
    QMatrix H(2,2);
    QMatrix X(2,2);
    QMatrix I(2,2);
    QMatrix CNOT(4,4);

    void init_gates() {
        const double invRoot2 = 1.0 / sqrt(2);

        // Hadamard
        H(0,0) = H(0,1) = H(1,0) = invRoot2;
        H(1,1) = -invRoot2;

        // Pauli-X
        X(0,0) = X(1,1) = 0;
        X(0,1) = X(1,0) = 1;

        // Identity
        I(0,0) = 1; I(1,1) = 1;

        // CNOT
        CNOT(0,0) = 1; 
        CNOT(1,1) = 1; 
        CNOT(2,3) = 1; 
        CNOT(3,2) = 1;
    }
}

// ---------------------- Grover Algorithm ----------------------
void oracle(vector<Complex> &state, int marked_index) {
    state[marked_index] *= -1.0;
}

vector<Complex> diffusion(const vector<Complex> &state) {
    int dim = state.size();
    Complex mean = 0;
    for(auto &amp : state) mean += amp;
    mean /= Complex(dim);

    vector<Complex> result(dim);
    for(int i = 0; i < dim; ++i)
        result[i] = 2.0*mean - state[i];

    return result;
}

vector<Complex> grover(int marked_index) {
    int n = 2;
    int dim = 1 << n;
    vector<Complex> state(dim, 0);
    state[0] = 1;

    QMatrix H2 = Gates::H * Gates::H;
    state = H2.multiply(state);

    int n_iter = int(round(sqrt(dim)));
    for(int i = 0; i < n_iter; ++i) {
        oracle(state, marked_index);
        state = diffusion(state);
    }

    return state;
}

int measure_state(const vector<Complex> &state) {
    int maxIndex = 0;
    double maxVal = abs(state[0]);
    for(int i = 1; i < state.size(); i++) {
        if(abs(state[i]) > maxVal) {
            maxVal = abs(state[i]);
            maxIndex = i;
        }
    }
    return maxIndex;
}

int bitstring_to_index(const string &s) {
    return stoi(s, nullptr, 2);
}

// ---------------------- Main ----------------------
int main() {
    Gates::init_gates();

    string marked_state_str;
    cout << "Enter 2-qubit marked state (e.g., 10): ";
    cin >> marked_state_str;
    int marked_index = bitstring_to_index(marked_state_str);

    vector<Complex> final_state = grover(marked_index);
    int measured_state = measure_state(final_state);

    // --- Serial connection to Arduino ---
    serial::Serial arduino("/dev/usbmodem11201", 9600, serial::Timeout::simpleTimeout(1000));
    arduino.write(to_string(measured_state) + "\n");
    cout << "Sent state index " << measured_state << " to Arduino.\n";

    return 0;
}
