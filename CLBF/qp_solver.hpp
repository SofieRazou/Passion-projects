#ifndef QP_SOLVER_HPP
#define QP_SOLVER_HPP

#include <Eigen/Dense>

using Vector = Eigen::VectorXd;
using Matrix = Eigen::MatrixXd;
using RowVector = Eigen::RowVectorXd;

/* =========================
         Abstract System
   ========================= */
class System {
public:
    virtual ~System() = default;

    virtual int stateDim() const = 0;
    virtual int inputDim() const = 0;

    virtual Vector f(const Vector& x) const = 0;
    virtual Matrix g(const Vector& x) const = 0;
};

/* =========================
       Concrete 2-state system
       x1_dot = x2
       x2_dot = u
   ========================= */
class DoubleIntegratorSystem : public System {
public:
    int stateDim() const override;
    int inputDim() const override;

    Vector f(const Vector& x) const override;
    Matrix g(const Vector& x) const override;
};

/* =========================
           CLF-QP Solver
   ========================= */
class Compute {
public:
    explicit Compute(double clf_rate = 1.0, double u_max = 10.0);

    double lie_f(const System& sys, const Vector& x) const;
    double lie_g(const System& sys, const Vector& x) const;
    double V(const Vector& x) const;

    double solve(const System& sys, const Vector& x) const;

private:
    double c_;      // CLF decay rate
    double umax_;   // input saturation
};

#endif