#include "qp_solver.hpp"

/* =========================
       Compute methods
  =========================
*/

double Compute::lie_f(const System& sys, const Vector& x) const {
    return grad(x).dot(sys.f(x));
}

RowVector Compute::lie_g(const System& sys, const Vector& x) const {
    return grad(x).transpose() * sys.g(x);
}

/* =========================
      QuadraticCLF methods
   =========================
*/
QuadraticCLF::QuadraticCLF(const Matrix& P, double c)
    : P_(P), c_(c) {}

double QuadraticCLF::value(const Vector& x) const {
    return (x.transpose() * P_ * x)(0, 0);
}

Vector QuadraticCLF::grad(const Vector& x) const {
    return 2.0 * P_ * x;
}

double QuadraticCLF::gamma(double Vx) const {
    return c_ * Vx;
}

/* =========================
        LinearCBF methods
   =========================
*/
LinearCBF::LinearCBF(const Vector& a, double b, double k)
    : a_(a), b_(b), k_(k) {}

double LinearCBF::value(const Vector& x) const {
    return a_.dot(x) + b_;
}

Vector LinearCBF::grad(const Vector& x) const {
    (void)x;
    return a_;
}

double LinearCBF::alpha(double hx) const {
    return k_ * hx;
}

/* =========================
      DummyQPSolver methods
   =========================
*/
Vector DummyQPSolver::solve(const System& sys, const Pformulation& qp) {
    (void)sys;
    return Vector::Zero(qp.H.rows());
}
