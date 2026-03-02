#pragma once

#include <tuple>
#include <vector>

struct State{
    double x, y, psi;

    State(double X=0.0, double Y=0.0, double h=0.0);
};

// free function operator==
bool operator==(const State &s1, const State &s2);

struct Control{
    double delta;
    double a;
};

struct weights{
    double Qx=1.0, Qy=1.0, Qpsi=0.1;
    double Rdelta=0.01, Ra=0.01;
    double Qfx=5.0, Qfy=5.0, Qfpsi=0.5;
    double smooth_delta=0.0, smooth_a=0.0;
    double collision=1000.0, d_safe=1.0;
};

// helpers (defined in .cpp)
double wrapAngle(double a);
double sq(double z);
double clampd(double x, double lo, double hi);

// A simple bound type
struct Bound { double lo, hi; };

class Car{
public:
    Car(State c, double v, double w);

    void reset(const State &s0);
    void setVelocity(double v);
    void setPosition(double x_, double y_);
    std::tuple<double, double, double> getPos() const;

    void step(const Control &u, double dt);

    double relative_dist(const Car &other) const;
    State snap() const;

    double objective_eval(
        const std::vector<double> &u_seq,
        const State &target,
        int H,
        const weights &w,
        double dt,
        const std::vector<Car> *others = nullptr
    ) const;

private:
    State s;
    double velocity;
    double wheelbase;
};

std::vector<double> PSO_best(
    int N,                 // particles
    int T,                 // iterations
    const std::vector<Bound> &bounds, // size D = 2*H
    const weights &wts,
    double c1, double c2,
    double inertia_w,
    double vmax,
    const Car &car,
    const State &target,
    int H,
    double dt,
    const std::vector<Car> *others = nullptr
);