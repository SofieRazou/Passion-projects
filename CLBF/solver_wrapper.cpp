#include "solver_wrapper.h"
#include "qp_solver.hpp"

double solve_qp_wrapper(double x1, double x2)
{
    Vector x(2);
    x << x1, x2;

    DoubleIntegratorSystem sys;
    Compute solver(100.0, 10.0);

    return solver.solve(sys, x);
}