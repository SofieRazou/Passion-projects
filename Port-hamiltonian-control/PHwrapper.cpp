// #include "PHwrapper.hpp"
// #include "PHham.hpp"
// #include <Eigen/Dense>
// #include <stdexcept>

// using Eigen::VectorXd;

// extern "C" void* createPlant(double M, double B, double K)
// {
//     try {
//         return static_cast<void*>(new PH(M, B, K));
//     } catch (...) {
//         return nullptr;
//     }
// }

// extern "C" void destroyPlant(void* plant)
// {
//     if (plant) {
//         delete static_cast<PH*>(plant);
//     }
// }

// extern "C" void* createController(void* plant, double kp, double ki, double kd)
// {
//     try {
//         if (!plant) return nullptr;
//         PH* p = static_cast<PH*>(plant);
//         return static_cast<void*>(new controller(*p, kp, ki, kd));
//     } catch (...) {
//         return nullptr;
//     }
// }

// extern "C" void destroyController(void* ctrl)
// {
//     if (ctrl) {
//         delete static_cast<controller*>(ctrl);
//     }
// }

// extern "C" void controllerReset(void* ctrl)
// {
//     if (!ctrl) return;
//     static_cast<controller*>(ctrl)->reset();
// }

// extern "C" void controllerSetRef(void* ctrl, double ref_q, double ref_p)
// {
//     if (!ctrl) return;

//     VectorXd x_ref(2);
//     x_ref << ref_q, ref_p;

//     static_cast<controller*>(ctrl)->setRef(x_ref);
// }

// extern "C" double controllerCompute(void* ctrl, double q, double p)
// {
//     if (!ctrl) return 0.0;

//     VectorXd x(2);
//     x << q, p;

//     VectorXd u = static_cast<controller*>(ctrl)->computeControl(x);
//     return u(0);
// }

// extern "C" double controllerEval(void* ctrl, double q, double p)
// {
//     if (!ctrl) return 0.0;

//     VectorXd x(2);
//     x << q, p;

//     return static_cast<controller*>(ctrl)->eval(x);
// }

// extern "C" void plantDynamics(void* plant, double q, double p, double u,
//                               double* dqdt, double* dpdt)
// {
//     if (!plant || !dqdt || !dpdt) return;

//     VectorXd x(2);
//     x << q, p;

//     VectorXd uu(1);
//     uu << u;

//     VectorXd dx = static_cast<PH*>(plant)->dynamics(x, uu);

//     *dqdt = dx(0);
//     *dpdt = dx(1);
// }

// extern "C" double plantOutput(void* plant, double q, double p)
// {
//     if (!plant) return 0.0;

//     VectorXd x(2);
//     x << q, p;

//     VectorXd y = static_cast<PH*>(plant)->output(x);
//     return y(0);
// }

// extern "C" double plantEnergy(void* plant, double q, double p)
// {
//     if (!plant) return 0.0;

//     VectorXd x(2);
//     x << q, p;

//     return static_cast<PH*>(plant)->H(x);
// }


#include "PHwrapper.hpp"
#include "PHham.hpp"
#include <Eigen/Dense>

using Eigen::VectorXd;

// u1 = q, u2 = p
// returns controller output u
extern "C" double PH_wrapper(double u1, double u2)
{
    // Fixed plant parameters
    PH plant(1.0, 0.02, 20.0);

    // Fixed controller gains
    controller ctrl(plant, 0.1, 0.01, 0.5);

    // Fixed reference state
    VectorXd x_ref(2);
    x_ref << 1.0, 5.0;
    ctrl.setRef(x_ref);

    // Current state
    VectorXd x(2);
    x << u1, u2;

    // Compute control
    VectorXd u = ctrl.computeControl(x);

    return u(0);
}