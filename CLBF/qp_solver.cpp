#include "qp_solver.hpp"
#include <algorithm>
#include <stdexcept>

/* =========================
     DoubleIntegratorSystem
   ========================= */

int DoubleIntegratorSystem::stateDim() const {
    return 2;
}

int DoubleIntegratorSystem::inputDim() const {
    return 1;
}

Vector DoubleIntegratorSystem::f(const Vector& x) const {
    if (x.size() != 2) {
        throw std::runtime_error("DoubleIntegratorSystem::f - x must have size 2");
    }

    Vector fx(2);
    fx << x(1), 0.0;
    return fx;
}

Matrix DoubleIntegratorSystem::g(const Vector& x) const {
    if (x.size() != 2) {
        throw std::runtime_error("DoubleIntegratorSystem::g - x must have size 2");
    }

    Matrix gx(2, 1);
    gx << 0.0,
          1.0;
    return gx;
}

/* =========================
           Compute
   ========================= */

Compute::Compute(double clf_rate, double u_max)
    : c_(clf_rate), umax_(u_max) {}

/*
    CLF:
    V(x) = 0.5 * (x1^2 + x2^2)

    gradV = [x1, x2]
*/
double Compute::V(const Vector& x) const {
    if (x.size() != 2) {
        throw std::runtime_error("Compute::V - x must have size 2");
    }

    return 0.5 * x.squaredNorm();
}

/*
    LfV = gradV * f(x)
*/
double Compute::lie_f(const System& sys, const Vector& x) const {
    if (x.size() != sys.stateDim()) {
        throw std::runtime_error("Compute::lie_f - state dimension mismatch");
    }

    Vector gradV(2);
    gradV << x(0), x(1);

    Vector fx = sys.f(x);
    return gradV.dot(fx);
}

/*
    LgV = gradV * g(x)
    Since u is scalar, g(x) is n x 1, result is scalar
*/
double Compute::lie_g(const System& sys, const Vector& x) const {
    if (x.size() != sys.stateDim()) {
        throw std::runtime_error("Compute::lie_g - state dimension mismatch");
    }

    Vector gradV(2);
    gradV << x(0), x(1);

    Matrix gx = sys.g(x);

    if (gx.cols() != 1) {
        throw std::runtime_error("Compute::lie_g - only scalar input supported");
    }

    return (gradV.transpose() * gx)(0, 0);
}

/*
    Solve simple 1D CLF-QP:

    minimize    0.5 * u^2
    subject to  LfV + LgV*u + c*V <= 0

    If LgV != 0, minimum norm solution is:
        u* = -(LfV + cV)/LgV
    whenever needed.

    If constraint already satisfied with u=0, return 0.
    Then saturate in [-umax, umax].
*/
double Compute::solve(const System& sys, const Vector& x) const {
    if (x.size() != sys.stateDim()) {
        throw std::runtime_error("Compute::solve - state dimension mismatch");
    }

    if (sys.inputDim() != 1) {
        throw std::runtime_error("Compute::solve - only scalar input supported");
    }

    const double Vx  = V(x);
    const double LfV = lie_f(sys, x);
    const double LgV = lie_g(sys, x);

    const double rhs = -(LfV + c_ * Vx);

    double u = 0.0;

    // If u = 0 already satisfies CLF inequality:
    // LfV + cV <= 0
    if (LfV + c_ * Vx <= 0.0) {
        u = 0.0;
    } else {
        // Need control action
        if (std::abs(LgV) < 1e-9) {
            // No authority through input at this state
            u = 0.0;
        } else {
            u = rhs / LgV;
        }
    }

    // Saturation
    u = std::max(-umax_, std::min(umax_, u));
    return u;
}