#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <cmath>
#include <vector>
#include <tuple>
#include <random>
#include <algorithm>
#include <limits>
#include <stdexcept>

#include "pso.hpp"

namespace py = pybind11;

// -------- helpers --------
double wrapAngle(double a){
    while(a > M_PI)  a -= 2.0*M_PI;
    while(a < -M_PI) a += 2.0*M_PI;
    return a;
}

double sq(double z){ return z*z; }

double clampd(double x, double lo, double hi){
    return std::max(lo, std::min(x, hi));
}

// -------- State --------
State::State(double X, double Y, double h): x(X), y(Y), psi(h) {}

bool operator==(const State &s1, const State &s2){
    return (s1.x == s2.x) && (s1.y == s2.y) && (s1.psi == s2.psi);
}

// -------- Car --------
Car::Car(State c, double v, double w): s(c), velocity(v), wheelbase(w) {}

void Car::reset(const State &s0){ s = s0; }
void Car::setVelocity(double v){ velocity = v; }
void Car::setPosition(double x_, double y_){ s.x = x_; s.y = y_; }

std::tuple<double,double,double> Car::getPos() const{
    return {s.x, s.y, s.psi};
}

void Car::step(const Control &u, double dt){
    if(dt <= 0.0) return;

    velocity += u.a * dt;

    const double psi_dot = (velocity / wheelbase) * std::tan(u.delta);
    s.psi += psi_dot * dt;

    // integrate
    s.x += velocity * std::cos(s.psi) * dt;
    s.y += velocity * std::sin(s.psi) * dt;
}

double Car::relative_dist(const Car &other) const{
    const double dx = s.x - std::get<0>(other.getPos());
    const double dy = s.y - std::get<1>(other.getPos());
    return std::sqrt(dx*dx + dy*dy);
}

State Car::snap() const { return s; }

double Car::objective_eval(
    const std::vector<double> &u_seq,
    const State &target,
    int H,
    const weights &w,
    double dt,
    const std::vector<Car> *others
) const {
    Car sim(this->snap(), this->velocity, this->wheelbase);

    double J = 0.0;
    double prev_delta = 0.0;
    double prev_a = 0.0;
    bool has_prev = false;

    for(int k=0; k<H; ++k){
        const double delta = u_seq[2*k];
        const double a     = u_seq[2*k+1];

        Control U{delta, a};
        sim.step(U, dt);

        const State sk = sim.snap();
        const double ex   = sk.x - target.x;
        const double ey   = sk.y - target.y;
        const double epsi = wrapAngle(sk.psi - target.psi);

        J += w.Qx*sq(ex) + w.Qy*sq(ey) + w.Qpsi*sq(epsi);
        J += w.Rdelta*sq(delta) + w.Ra*sq(a);

        if(has_prev){
            J += w.smooth_delta * sq(delta - prev_delta);
            J += w.smooth_a     * sq(a     - prev_a);
        }
        prev_delta = delta;
        prev_a = a;
        has_prev = true;

        if(others){
            for(const auto &car : *others){
                const double dx = sk.x - std::get<0>(car.getPos());
                const double dy = sk.y - std::get<1>(car.getPos());
                const double d  = std::sqrt(dx*dx + dy*dy);
                if(d < w.d_safe){
                    J += w.collision * sq(w.d_safe - d);
                }
            }
        }
    }

    // terminal cost
    const State sH = sim.snap();
    const double ex   = sH.x - target.x;
    const double ey   = sH.y - target.y;
    const double epsi = wrapAngle(sH.psi - target.psi);

    J += w.Qfx*sq(ex) + w.Qfy*sq(ey) + w.Qfpsi*sq(epsi);

    return J;
}

// -------- PSO --------
std::vector<double> PSO_best(
    int N,
    int T,
    const std::vector<Bound> &bounds,
    const weights &wts,
    double c1, double c2,
    double inertia_w,
    double vmax,
    const Car &car,
    const State &target,
    int H,
    double dt,
    const std::vector<Car> *others
){
    const int D = (int)bounds.size();
    if(D != 2*H){
        throw std::runtime_error("bounds.size() must be 2*H (delta,a for each step)");
    }

    std::mt19937 gen(std::random_device{}());
    std::uniform_real_distribution<double> uni01(0.0, 1.0);

    auto randIn = [&](double lo, double hi){
        std::uniform_real_distribution<double> u(lo, hi);
        return u(gen);
    };

    std::vector<std::vector<double>> x(N, std::vector<double>(D, 0.0));
    std::vector<std::vector<double>> v(N, std::vector<double>(D, 0.0));

    std::vector<std::vector<double>> pbest(N, std::vector<double>(D, 0.0));
    std::vector<double> pbestVal(N, std::numeric_limits<double>::infinity());

    std::vector<double> gbest(D, 0.0);
    double gbestVal = std::numeric_limits<double>::infinity();

    // init
    for(int i=0;i<N;++i){
        for(int j=0;j<D;++j){
            x[i][j] = randIn(bounds[j].lo, bounds[j].hi);
            v[i][j] = randIn(-vmax, vmax);
        }
        pbest[i] = x[i];
        pbestVal[i] = car.objective_eval(x[i], target, H, wts, dt, others);

        if(pbestVal[i] < gbestVal){
            gbestVal = pbestVal[i];
            gbest = pbest[i];
        }
    }

    // iterate
    for(int t=0;t<T;++t){
        for(int i=0;i<N;++i){
            for(int j=0;j<D;++j){
                const double r1 = uni01(gen);
                const double r2 = uni01(gen);

                v[i][j] = inertia_w * v[i][j]
                        + c1 * r1 * (pbest[i][j] - x[i][j])
                        + c2 * r2 * (gbest[j]    - x[i][j]);

                v[i][j] = clampd(v[i][j], -vmax, vmax);

                x[i][j] = clampd(x[i][j] + v[i][j], bounds[j].lo, bounds[j].hi);
            }

            const double val = car.objective_eval(x[i], target, H, wts, dt, others);

            if(val < pbestVal[i]){
                pbestVal[i] = val;
                pbest[i] = x[i];
            }
            if(val < gbestVal){
                gbestVal = val;
                gbest = x[i];
            }
        }
    }

    return gbest;
}

// -------- pybind11 module --------
PYBIND11_MODULE(pso_module, m) {
    m.doc() = "Car PSO algorithm simulation wrapped with pybind11";

    py::class_<State>(m, "State")
        .def(py::init<double,double,double>(), py::arg("x")=0.0, py::arg("y")=0.0, py::arg("psi")=0.0)
        .def_readwrite("x", &State::x)
        .def_readwrite("y", &State::y)
        .def_readwrite("psi", &State::psi);

    py::class_<Control>(m, "Control")
        .def(py::init<>())
        .def_readwrite("delta", &Control::delta)
        .def_readwrite("a", &Control::a);

    py::class_<weights>(m, "weights")
        .def(py::init<>())
        .def_readwrite("Qx", &weights::Qx)
        .def_readwrite("Qy", &weights::Qy)
        .def_readwrite("Qpsi", &weights::Qpsi)
        .def_readwrite("Rdelta", &weights::Rdelta)
        .def_readwrite("Ra", &weights::Ra)
        .def_readwrite("Qfx", &weights::Qfx)
        .def_readwrite("Qfy", &weights::Qfy)
        .def_readwrite("Qfpsi", &weights::Qfpsi)
        .def_readwrite("smooth_delta", &weights::smooth_delta)
        .def_readwrite("smooth_a", &weights::smooth_a)
        .def_readwrite("collision", &weights::collision)
        .def_readwrite("d_safe", &weights::d_safe);

    py::class_<Bound>(m, "Bound")
        .def(py::init<>())
        .def_readwrite("lo", &Bound::lo)
        .def_readwrite("hi", &Bound::hi);

    py::class_<Car>(m, "Car")
        .def(py::init<State,double,double>())
        .def("reset", &Car::reset)
        .def("setVelocity", &Car::setVelocity)
        .def("setPosition", &Car::setPosition)
        .def("getPos", &Car::getPos)
        .def("step", &Car::step)
        .def("relative_dist", &Car::relative_dist)
        .def("snap", &Car::snap)
        .def("objective_eval", &Car::objective_eval,
             py::arg("u_seq"), py::arg("target"), py::arg("H"), py::arg("w"), py::arg("dt"),
             py::arg("others") = (const std::vector<Car>*)nullptr);

    m.def("PSO_best", &PSO_best,
          py::arg("N"), py::arg("T"), py::arg("bounds"), py::arg("wts"),
          py::arg("c1"), py::arg("c2"), py::arg("inertia_w"), py::arg("vmax"),
          py::arg("car"), py::arg("target"), py::arg("H"), py::arg("dt"),
          py::arg("others") = (const std::vector<Car>*)nullptr,
          "Compute PSO best control sequence");
}