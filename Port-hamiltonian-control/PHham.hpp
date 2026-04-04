#ifndef PHHAM_HPP
#define PHHAM_HPP

#include <iostream>
#include <cmath>
#include <vector>
#include <ostream>
#include <stdexcept>
#include <Eigen/Dense>

using Eigen::VectorXd;
using Eigen::MatrixXd;

// Universal effort-flow port
struct Port {
    VectorXd effort;
    VectorXd flow;

    // Operational checks
    bool isValid() const;
    int dim() const;

    // Instantaneous power = effort^T * flow
    double power() const;
};


// Concrete 1-DOF port-Hamiltonian system
// State: x = [q, p]^T
class PH {
public:
    PH(double m, double b, double k);

    double H(const VectorXd& state) const;
    VectorXd gradH(const VectorXd& state) const;

    MatrixXd J() const;
    MatrixXd R() const;
    MatrixXd G() const;

    VectorXd dynamics(const VectorXd& x, const VectorXd& u) const;
    VectorXd output(const VectorXd& x) const;

    bool checkSkew() const;
    bool checkDissipation() const;

    // Getters
    int getStateDim() const;
    int getInputDim() const;
    int getOutputDim() const;

    // Logging
    friend std::ostream& operator<<(std::ostream& os, const PH& sys);

protected:
    std::vector<Port> ports;

    int stateDim;
    int inputDim;
    int outputDim;

    double M;
    double B;
    double K;
};


// A spin-off of a PI/PID-style controller with PH flavor
class controller {
public:
    controller(const PH& p, double kp, double ki, double kd);

    VectorXd computeControl(const VectorXd& x);

    void reset();
    double eval(const VectorXd& x) const;
    void setRef(const VectorXd& x_ref);

private:
    const PH& plant;

    double Kp;
    double Ki;
    double Kd;

    VectorXd x_ref;

    double integralError;
    double prevError;
    bool hasPrev;

    bool checkPassivity() const;
};

#endif