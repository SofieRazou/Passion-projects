#include<iostream>
#include<cmath>
#include<complex>
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
