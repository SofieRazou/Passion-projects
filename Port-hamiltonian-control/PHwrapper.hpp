#ifndef WRAPPER_HPP
#define WRAPPER_HPP

#ifdef __cplusplus
extern "C" {
#endif

// Opaque handles
void* createPlant(double M, double B, double K);
void destroyPlant(void* plant);

void* createController(void* plant, double kp, double ki, double kd);
void destroyController(void* ctrl);

// Controller interface
void controllerReset(void* ctrl);
void controllerSetRef(void* ctrl, double ref_q, double ref_p);
double controllerCompute(void* ctrl, double q, double p);
double controllerEval(void* ctrl, double q, double p);

// Plant interface
void plantDynamics(void* plant, double q, double p, double u,
                   double* dqdt, double* dpdt);

double plantOutput(void* plant, double q, double p);
double plantEnergy(void* plant, double q, double p);

extern "C" double PH_wrapper(double u1, double u2);
#ifdef __cplusplus
}
#endif

#endif