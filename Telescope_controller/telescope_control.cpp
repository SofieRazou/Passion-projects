#include<iostream>
#include<cmath>
#include<vector>
#include<map>
#include<utility>
#include<algorithm>
#include<stdexcept>
#include<fstream>
#include<expected>
using namespace std;

const double PI = 3.14159;

void normaliseAngle(double &az, double &el){
    az = fmod(az, 360.0);
    if (az < 0) az += 360.0;
    el = fmod(el, 180.0);
    if (el < 0) el += 180.0;
}

class CelBod{
    private:
        double azimuth, elevation;
        string type, name;
        vector<CelBod> adj;
        void sortD(vector<CelBod> &list){
            sort(list.begin(), list.end(), [this](const CelBod &c1, const CelBod &c2){
                return this->getAngularDistance(c1) < this->getAngularDistance(c2);
            });
        }
    public:
        CelBod(double a, double e, string type, string name): azimuth(a), elevation(e), type(type), name(name){}
        
        pair<double,double> getCoords(){
            return {azimuth, elevation};
        }

        string getType(){
            return type;
        }

        string getName(){
            return name;
        }

        void addAdjacent(const CelBod &c){
            adj.push_back(c);
        }

        vector<CelBod> getNearest(int numnear){
            if(numnear > adj.size())
                throw logic_error("Invalid number of celestial bodies selected.");
            sortD(adj);
            return vector<CelBod>(adj.begin(), adj.begin() + numnear);
        }

        double getAngularDistance(const CelBod &c){
            double az = abs(azimuth - c.azimuth);
            double el = abs(elevation - c.elevation);
            return sqrt(pow(az, 2) + pow(el, 2));
        }
};

class PID{
    private:
        double Kp, Ki, Kd;
        double prevErr = 0, integral = 0;

    public:
        PID(double p, double i, double d): Kp(p), Ki(i), Kd(d){}

        double update(double error, double dt){
            integral += error * dt;
            double derivative = (error - prevErr) / dt;
            prevErr = error;
            return Kp * error + Ki * integral + Kd * derivative;
        }

        void reset(){
            prevErr = 0;
            integral = 0;
        }
};

class Move{
    protected:
        double azimuth;
        double elevation;

    public:
        Move(): azimuth(0.0), elevation(0.0){}

        pair<double, double> getPos(){
            return {azimuth, elevation};
        }

        void setPos(double a, double e){
            azimuth = a;
            elevation = e;
        }

        virtual void updatePos(double az_vel, double el_vel, double dt){
            azimuth += az_vel * dt;
            elevation += el_vel * dt;
        }
};

class Tele: public Move{
    private:
        PID az_pid;
        PID el_pid;
        double target_az, target_el;

    public:
        Tele(double a, double e, PID az_pid, PID el_pid): az_pid(az_pid), el_pid(el_pid){
            setPos(a, e);
        }

        void setTarget(double taz, double tel){
            target_az = taz;
            target_el = tel;
        }

        void track(double dt){
            double az_error = target_az - azimuth;
            double el_error = target_el - elevation;

            double az_vel = az_pid.update(az_error, dt);
            double el_vel = el_pid.update(el_error, dt);

            updatePos(az_vel, el_vel, dt);
        }
};


int main() {
    ofstream f("data.txt", ios::trunc);
    if (!f.is_open())
        throw runtime_error("Data file not opened properly");

    PID az_pid(0.1, 0.01, 0.05);
    PID el_pid(0.1, 0.01, 0.05);
    Tele telescope(0.0, 0.0, az_pid, el_pid);
    telescope.setTarget(30.0, 45.0);

    double dt = 0.1;
    for (int step = 0; step < dt * 1000; ++step) {
        telescope.track(dt);
        auto [az, el] = telescope.getPos();

        // Write to file
        f <<"Azimuth"<< az << "," <<"Elevation"<<el << "\n";

        cout << "Step " << step << ": Azimuth = " << az << ", Elevation = " << el << endl;

        if (abs(az - 30.0) < 0.01 && abs(el - 45.0) < 0.01) {
            cout << "Target reached!\n";
            break;
        }
    }

    f.close();
    return 0;
}
