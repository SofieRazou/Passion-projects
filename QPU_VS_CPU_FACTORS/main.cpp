#include <pybind11/pybind11.h>
#include "cpu_actual.hpp"
#include "gpu_virtual.hpp"

namespace py = pybind11;

long long GNFS_small_wrapper(long long N) {
    return GNFS_small(N);
}

int Shors_wrapper(int N) {
    return Shors(N);
}

PYBIND11_MODULE(my_module, m) {
    m.doc() = "C++ number theory algorithms wrapped with pybind11";

    m.def("GNFS_small", &GNFS_small_wrapper, "Compute GNFS_small on a given number N");
    m.def("Shors", &Shors_wrapper, "Run Shor's algorithm to factor N");
}