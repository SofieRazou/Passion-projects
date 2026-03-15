#include <iostream>
#include "qp_solver.hpp"

using std::cout;
using std::endl;

/* =========================
        Test System
   =========================
   Double Integrator

   x1_dot = x2
   x2_dot = u
*/
class DoubleIntegrator : public System {
public:
    int stateDim() const override { return 2; }
    int inputDim() const override { return 1; }

    Vector f(const Vector& x) const override {
        Vector fx(2);
        fx << x(1), 0.0;
        return fx;
    }

    Matrix g(const Vector& x) const override {
        (void)x;
        Matrix gx(2,1);
        gx << 0.0,
              1.0;
        return gx;
    }
};

int main() {

    cout << "===== CLF-CBF-QP TEST =====" << endl;

    /* =========================
        Create system
    =========================
    */
    DoubleIntegrator sys;

    cout << "State dimension: " << sys.stateDim() << endl;
    cout << "Input dimension: " << sys.inputDim() << endl;

    /* =========================
        Test state
    =========================
    */
    Vector x(2);
    x << 1.0, -0.5;

    cout << "\nState x:\n" << x << endl;

    /* =========================
        Create CLF
    =========================
    */
    Matrix P = Matrix::Identity(2,2);
    QuadraticCLF clf(P, 1.0);

    double V = clf.value(x);
    Vector gradV = clf.grad(x);

    cout << "\nCLF V(x): " << V << endl;
    cout << "grad V:\n" << gradV << endl;

    /* =========================
        Lie derivatives
    =========================
    */
    double LfV = clf.lie_f(sys, x);
    RowVector LgV = clf.lie_g(sys, x);

    cout << "\nLfV: " << LfV << endl;
    cout << "LgV: " << LgV << endl;

    /* =========================
        Create CBF
    =========================
       Example:
       h(x) = 2 - x1
       keeps x1 <= 2
    */
    Vector a(2);
    a << -1.0, 0.0;

    LinearCBF cbf(a, 2.0, 2.0);

    double h = cbf.value(x);
    Vector gradh = cbf.grad(x);

    cout << "\nCBF h(x): " << h << endl;
    cout << "grad h:\n" << gradh << endl;

    double Lfh = cbf.lie_f(sys, x);
    RowVector Lgh = cbf.lie_g(sys, x);

    cout << "\nLfh: " << Lfh << endl;
    cout << "Lgh: " << Lgh << endl;

    /* =========================
        Build simple QP
    =========================
    */

    int m = sys.inputDim();

    Matrix H = Matrix::Identity(m+1, m+1);
    Vector q = Vector::Zero(m+1);

    Matrix A(2, m+1);
    Vector b(2);

    // CLF constraint
    A(0,0) = LgV(0);
    A(0,1) = -1.0;

    b(0) = -LfV - clf.gamma(V);

    // input upper bound u <= 5
    A(1,0) = 1.0;
    A(1,1) = 0.0;

    b(1) = 5.0;

    Pformulation qp(H,q,A,b,0.0);

    cout << "\nQP matrices:" << endl;

    cout << "\nH:\n" << qp.H << endl;
    cout << "\nA:\n" << qp.A << endl;
    cout << "\nb:\n" << qp.b << endl;

    /* =========================
        Solve QP
    =========================
    */

    DummyQPSolver solver;

    Vector z = solver.solve(sys, qp);

    cout << "\nSolver output z:\n" << z << endl;

    cout << "\nControl input u* = " << z(0) << endl;

    cout << "\n===== TEST COMPLETE =====" << endl;

    return 0;
}
