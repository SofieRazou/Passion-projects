#include "PHham.hpp"
#include <stdexcept>
#include <Eigen/Eigenvalues>

// ======================
// Port method implementation
// ======================

bool Port::isValid() const {
    return (effort.size() == flow.size()) && (effort.size() > 0);
}

int Port::dim() const {
    return isValid() ? static_cast<int>(effort.size()) : -1;
}

double Port::power() const {
    if (!isValid()) {
        throw std::runtime_error("Invalid port: effort and flow must have same nonzero dimension.");
    }
    return effort.dot(flow);
}


// ======================
// PH class implementation
// ======================

PH::PH(double m, double b, double k)
    : M(m), B(b), K(k), stateDim(2), inputDim(1), outputDim(1) {
    if (M <= 0.0) {
        throw std::runtime_error("M must be positive.");
    }
    if (B < 0.0) {
        throw std::runtime_error("B must be nonnegative.");
    }
    if (K < 0.0) {
        throw std::runtime_error("K must be nonnegative.");
    }
}

double PH::H(const VectorXd& state) const {
    if (state.size() != stateDim) {
        throw std::runtime_error("State dimension mismatch in H().");
    }

    double q = state(0);
    double p = state(1);

    return 0.5 * K * q * q + 0.5 * (p * p) / M;
}

VectorXd PH::gradH(const VectorXd& state) const {
    if (state.size() != stateDim) {
        throw std::runtime_error("State dimension mismatch in gradH().");
    }

    double q = state(0);
    double p = state(1);

    VectorXd g(2);
    g << K * q,
         p / M;
    return g;
}

MatrixXd PH::J() const {
    MatrixXd Jmat(2, 2);
    Jmat <<  0.0,  1.0,
            -1.0,  0.0;
    return Jmat;
}

MatrixXd PH::R() const {
    MatrixXd Rmat(2, 2);
    Rmat << 0.0, 0.0,
            0.0, B;
    return Rmat;
}

MatrixXd PH::G() const {
    MatrixXd Gmat(2, 1);
    Gmat << 0.0,
            1.0;
    return Gmat;
}

VectorXd PH::dynamics(const VectorXd& x, const VectorXd& u) const {
    if (x.size() != stateDim) {
        throw std::runtime_error("State dimension mismatch in dynamics().");
    }
    if (u.size() != inputDim) {
        throw std::runtime_error("Input dimension mismatch in dynamics().");
    }

    return (J() - R()) * gradH(x) + G() * u;
}

VectorXd PH::output(const VectorXd& x) const {
    if (x.size() != stateDim) {
        throw std::runtime_error("State dimension mismatch in output().");
    }

    return G().transpose() * gradH(x);
}

bool PH::checkSkew() const {
    MatrixXd test = J() + J().transpose();
    return test.norm() < 1e-8;
}

bool PH::checkDissipation() const {
    MatrixXd Rmat = R();

    if (!Rmat.isApprox(Rmat.transpose(), 1e-8)) {
        return false;
    }

    Eigen::SelfAdjointEigenSolver<MatrixXd> solver(Rmat);
    if (solver.info() != Eigen::Success) {
        return false;
    }

    return solver.eigenvalues().minCoeff() >= -1e-8;
}


// ======================
// Getters
// ======================

int PH::getStateDim() const {
    return stateDim;
}

int PH::getInputDim() const {
    return inputDim;
}

int PH::getOutputDim() const {
    return outputDim;
}


// ======================
// Logging
// ======================

std::ostream& operator<<(std::ostream& os, const PH& sys) {
    os << "PH System [1-DOF]"
       << "\nM = " << sys.M
       << "\nB = " << sys.B
       << "\nK = " << sys.K
       << "\nstateDim = " << sys.stateDim
       << "\ninputDim = " << sys.inputDim
       << "\noutputDim = " << sys.outputDim;
    return os;
}


// ======================
// Controller implementation
// ======================

controller::controller(const PH& p, double kp, double ki, double kd)
    : plant(p),
      Kp(kp),
      Ki(ki),
      Kd(kd),
      x_ref(VectorXd::Zero(p.getStateDim())),
      integralError(0.0),
      prevError(0.0),
      hasPrev(false) {
    if (Kp < 0.0 || Ki < 0.0 || Kd < 0.0) {
        throw std::runtime_error("Controller gains must be nonnegative.");
    }
}

VectorXd controller::computeControl(const VectorXd& x) {
    if (x.size() != plant.getStateDim()) {
        throw std::runtime_error("State dimension mismatch in computeControl().");
    }

    if (x_ref.size() != plant.getStateDim()) {
        throw std::runtime_error("Reference dimension mismatch in computeControl().");
    }

    // 1-DOF PH system state:
    // x(0) = q, x(1) = p
    // control acts on position tracking
    double q     = x(0);
    double q_ref_val = x_ref(0);

    double error = q_ref_val - q;

    integralError += error;

    double derivativeError = 0.0;
    if (hasPrev) {
        derivativeError = error - prevError;
    }

    prevError = error;
    hasPrev = true;

    VectorXd u(plant.getInputDim());
    u(0) = Kp * error + Ki * integralError + Kd * derivativeError;

    return u;
}

void controller::reset() {
    integralError = 0.0;
    prevError = 0.0;
    hasPrev = false;
}

double controller::eval(const VectorXd& x) const {
    if (x.size() != plant.getStateDim()) {
        throw std::runtime_error("State dimension mismatch in eval().");
    }

    if (x_ref.size() != plant.getStateDim()) {
        throw std::runtime_error("Reference dimension mismatch in eval().");
    }

    double error = x_ref(0) - x(0);
    return 0.5 * error * error;
}

void controller::setRef(const VectorXd& ref) {
    if (ref.size() != plant.getStateDim()) {
        throw std::runtime_error("Reference dimension mismatch in setRef().");
    }

    x_ref = ref;
}

bool controller::checkPassivity() const {
    return (Kp >= 0.0 && Ki >= 0.0 && Kd >= 0.0);
}

//test main 
void PH_test() {
    PH plant(1.0, 0.02, 20.0);
    controller c(plant, 0.1, 0.01, 0.5);

    c.reset();

    // State x = [q, p]^T
    Eigen::VectorXd state_0(2);
    state_0 << 0.01, 0.0;

    // Reference state x_ref = [q_ref, p_ref]^T
    Eigen::VectorXd x_ref(2);
    x_ref << 4.0, 5.0;

    c.setRef(x_ref);

    Eigen::VectorXd u = c.computeControl(state_0);
    double cost = c.eval(state_0);

    std::cout << plant << std::endl;
    std::cout << "Initial state:\n" << state_0 << std::endl;
    std::cout << "Reference state:\n" << x_ref << std::endl;
    std::cout << "Control input u:\n" << u << std::endl;
    std::cout << "Tracking cost:\n" << cost << std::endl;

}