#pragma once
#include <vector>

// ----------------------------
// Polynomial struct
// ----------------------------
struct Poly {
    long long c2, c1, c0; // degree 2: f(x) = c2*x^2 + c1*x + c0

    long long eval(long long x);
    void print();
};

// ----------------------------
// Simple prime sieve
// ----------------------------
std::vector<int> prime_sieve(int limit);

// ----------------------------
// Generate candidate polynomial
// ----------------------------
Poly choose_polynomial(long long N);

// ----------------------------
// Check if a number is B-smooth
// ----------------------------
bool is_smooth(long long n, const std::vector<int>& factor_base);

// ----------------------------
// GNFS simulation for small N
// ----------------------------
long long GNFS_small(long long N);