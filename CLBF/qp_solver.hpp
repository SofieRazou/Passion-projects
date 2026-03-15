#pragma once

#include <Eigen/Dense>
#include <memory>
#include <vector>

using Vector = Eigen::VectorXd;
using Matrix = Eigen::MatrixXd;
using RowVector = Eigen::RowVectorXd;

/* =========================
            State
   =========================
*/
struct State {
    Vector x;

    State() = default;
    explicit State(const Vector& X) : x(X) {}

    int size() const {
        return static_cast<int>(x.size());
    }
};

/* =========================
 Abstract control-affine system
   =========================
*/
class System {
public:
    virtual ~System() = default;

    virtual int stateDim() const = 0;
    virtual int inputDim() const = 0;

    virtual Vector f(const Vector& x) const = 0;
    virtual Matrix g(const Vector& x) const = 0;
};

/* =========================
   Abstract scalar function
   =========================
*/
class Compute {
public:
    virtual ~Compute() = default;
    virtual double value(const Vector& x) const = 0;
    virtual Vector grad(const Vector& x) const = 0;

    double lie_f(const System& sys, const Vector& x) const;
    RowVector lie_g(const System& sys, const Vector& x) const;
};

/* =========================
             CLF
   =========================
*/
class CLF : public Compute {
public:
    virtual ~CLF() = default;
    virtual double gamma(double Vx) const = 0;
};

/* =========================
              CBF
   =========================
*/
class CBF : public Compute {
public:
    virtual ~CBF() = default;
    virtual double alpha(double hx) const = 0;
};

/* =========================
        QP formulation
   =========================
*/
struct Pformulation {
    Matrix H;
    Vector q;
    Matrix A;
    Vector b;
    double delta;

    Pformulation() = default;

    Pformulation(const Matrix& H_,
                 const Vector& q_,
                 const Matrix& A_,
                 const Vector& b_,
                 double d)
        : H(H_), q(q_), A(A_), b(b_), delta(d) {}
};

/* =========================
     QP solver interface
  =========================
*/
class QPsolver {
public:
    QPsolver() = default;
    virtual ~QPsolver() = default;

    virtual Vector solve(const System& sys, const Pformulation& qp) = 0;
};


/* =========================
      Concrete Quadratic CLF
   =========================
*/
class QuadraticCLF : public CLF {
private:
    Matrix P_;
    double c_;

public:
    QuadraticCLF(const Matrix& P, double c);

    double value(const Vector& x) const override;
    Vector grad(const Vector& x) const override;
    double gamma(double Vx) const override;
};

/* =========================
       Concrete Linear CBF
   =========================
*/
class LinearCBF : public CBF {
private:
    Vector a_;
    double b_;
    double k_;

public:
    LinearCBF(const Vector& a, double b, double k);

    double value(const Vector& x) const override;
    Vector grad(const Vector& x) const override;
    double alpha(double hx) const override;
};

/* =========================
         Dummy QP Solver
   =========================
*/
class DummyQPSolver : public QPsolver {
public:
    Vector solve(const System& sys, const Pformulation& qp) override;
};
