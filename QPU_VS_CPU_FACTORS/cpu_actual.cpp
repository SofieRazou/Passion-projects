#include "cpu_actual.hpp"
#include <iostream>
#include <cmath>
#include <random>
#include <algorithm>
#include <numeric>

using namespace std;

// ----------------------------
// Poly member functions
// ----------------------------
long long Poly::eval(long long x) {
    return c2*x*x + c1*x + c0;
}

void Poly::print() {
    cout << "f(x) = " << c2 << "x^2 + " << c1 << "x + " << c0 << endl;
}

// ----------------------------
// Simple prime sieve
// ----------------------------
vector<int> prime_sieve(int limit) {
    vector<bool> is_prime(limit+1, true);
    is_prime[0] = is_prime[1] = false;
    for(int i=2;i*i<=limit;i++)
        if(is_prime[i])
            for(int j=i*i;j<=limit;j+=i) is_prime[j]=false;
    vector<int> primes;
    for(int i=2;i<=limit;i++) if(is_prime[i]) primes.push_back(i);
    return primes;
}

// ----------------------------
// Generate candidate polynomial
// ----------------------------
Poly choose_polynomial(long long N) {
    mt19937 gen(random_device{}());
    uniform_int_distribution<long long> dis(1, 10);

    int d = 2; // degree
    long long m = round(pow(N, 1.0/d));

    long long c2 = dis(gen);
    long long c1 = dis(gen);
    long long c0 = (- (c2*m*m + c1*m)) % N;
    if(c0 < 0) c0 += N;

    return Poly{c2, c1, c0};
}

// ----------------------------
// Check if a number is B-smooth
// ----------------------------
bool is_smooth(long long n, const vector<int>& factor_base) {
    if(n<0) n=-n;
    for(int p: factor_base) {
        while(n%p==0) n/=p;
    }
    return n==1;
}

// ----------------------------
// GNFS simulation for small N
// ----------------------------
long long GNFS_small(long long N) {
    // Step 1: polynomial
    Poly f = choose_polynomial(N);
    f.print();

    // Step 2: factor base
    int B = 20; // small primes for small N
    vector<int> FB = prime_sieve(B);

    cout << "Factor base: ";
    for(int p: FB) cout << p << " ";
    cout << endl;

    // Step 3: sieving for smooth relations
    vector<pair<long long,long long>> relations;
    long long m = round(pow(N,1.0/2));

    for(long long a=m-50; a<=m+50; a++) {
        long long val = f.eval(a);
        if(is_smooth(val, FB)) {
            relations.push_back({a,val});
            cout << "Found smooth: f(" << a << ")=" << val << endl;
        }
        if(relations.size()>=5) break; // just a few for demo
    }

    // Step 4: combine two relations to find factor
    for(int i=0;i<relations.size();i++) {
        for(int j=i+1;j<relations.size();j++) {
            long long x = relations[i].first - m;
            long long y = relations[j].first - m;
            long long g = gcd(x-y,N);
            if(g!=1 && g!=N) return g;
        }
    }

    return -1; // failed
}

// ----------------------------
// Main
// ----------------------------
// int main() {
//     long long N = 91; // number to factor
//     long long factor = GNFS_small(N);

//     if(factor>0)
//         cout << "Found factor of " << N << " : " << factor << endl;
//     else
//         cout << "Failed to find factor." << endl;

//     return 0;
// }