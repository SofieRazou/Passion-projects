#include <iostream>
#include <cmath>

using namespace std;

const int N = 19;
const int M = 5;

double D_vals[M] = {30.0, 20.0, 15.0, 10.0, 5.0};

double measurements[M][N] = {
    {27.54, 28.85, 29.82, 27.42, 27.54, 27.42, 27.54, 27.44, 27.53,
     27.42, 27.53, 27.44, 27.53, 27.44, 27.44, 27.54, 27.44, 29.46, 29.98},

    {19.38, 20.24, 20.25, 19.07, 20.34, 20.36, 20.36, 20.34, 20.36,
     20.36, 20.24, 20.25, 20.34, 20.36, 20.36, 20.34, 20.34, 19.07, 20.36},

    {16.17, 14.56, 14.46, 14.46, 16.19, 16.17, 16.28, 14.46, 16.19,
     16.19, 14.80, 14.90, 16.19, 25.40, 24.63, 24.63, 16.17, 24.52, 24.52},

    {11.64, 11.75, 11.64, 11.75, 9.90, 10.00, 9.90, 10.00, 9.90,
     10.00, 10.24, 10.36, 10.24, 10.36, 10.24, 10.36, 10.26, 10.36, 10.24},

    {4.37, 4.37, 4.37, 4.29, 4.27, 4.37, 4.37, 4.37, 4.37,
     4.39, 4.37, 4.27, 4.27, 4.37, 4.37, 4.37, 4.37, 4.37, 5.68}
};

struct GlobalMLEGaussian {
    double mu_error;
    double sigma_error;
};

GlobalMLEGaussian fitGlobalMLE() {
    int total = M * N;

    double sumError = 0.0;

    for (int j = 0; j < M; j++) {
        for (int i = 0; i < N; i++) {
            double error = measurements[j][i] - D_vals[j];
            sumError += error;
        }
    }

    double mu = sumError / total;

    double variance = 0.0;

    for (int j = 0; j < M; j++) {
        for (int i = 0; i < N; i++) {
            double error = measurements[j][i] - D_vals[j];
            variance += pow(error - mu, 2.0);
        }
    }

    // MLE uses total, not total - 1
    variance /= total;

    double sigma = sqrt(variance);

    if (sigma < 1e-6) {
        sigma = 1e-6;
    }

    return {mu, sigma};
}

int main() {
    GlobalMLEGaussian model = fitGlobalMLE();

    cout << "Final MLE ultrasonic Gaussian error model:" << endl;
    cout << "z = d + error" << endl;
    cout << "error ~ N(mu_error, sigma_error^2)" << endl;
    cout << "mu_error = " << model.mu_error << " cm" << endl;
    cout << "sigma_error = " << model.sigma_error << " cm" << endl;

    double z;

    cout << endl;
    cout << "Enter ultrasonic measurement z: ";
    cin >> z;

    double d_mle = z - model.mu_error;

    cout << endl;
    cout << "Measurement z = " << z << " cm" << endl;
    cout << "MLE estimated real distance = " << d_mle << " cm" << endl;

    cout << endl;
    cout << "Use in your Simulink/ultrasonic model:" << endl;
    cout << "mu = " << model.mu_error << endl;
    cout << "sigma = " << model.sigma_error << endl;

    return 0;
}