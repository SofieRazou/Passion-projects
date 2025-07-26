#include <iostream>
#include <fstream>
#include "Pythia8/Pythia.h"

int main() {
    using namespace Pythia8;

    int nevents = 1000;
    Pythia pythia;

    // Proton-proton beams, 6.3 TeV CM energy
    pythia.readString("Beams:idA = 2212");
    pythia.readString("Beams:idB = 2212");
    pythia.readString("Beams:eCM = 6300.");

    // Enable Higgs production via gluon fusion
    pythia.readString("HiggsSM:gg2H = on");

    // Higgs → a a
    pythia.readString("35:onMode = off");
    pythia.readString("35:onIfMatch = 36 36");

    // a → b b̄
    pythia.readString("36:onMode = off");
    pythia.readString("36:onIfMatch = 5 -5");

    if (!pythia.init()) {
        std::cerr << "Pythia initialization failed!" << std::endl;
        return 1;
    }

    std::ofstream outfile("event_data.csv");
    outfile << "event_id,particle_id,status,px,py,pz,e,m,pT\n";

    for (int i = 0; i < nevents; ++i) {
        if (!pythia.next()) continue;

        for (int j = 0; j < pythia.event.size(); ++j) {
            auto& p = pythia.event[j];

            // Save all final-state particles (status 1)
            if (!p.isFinal()) continue;

            outfile << i + 1 << ","
                    << p.id() << ","
                    << p.status() << ","
                    << p.px() << ","
                    << p.py() << ","
                    << p.pz() << ","
                    << p.e() << ","
                    << p.m() << ","
                    << p.pT() << "\n";
        }
    }

    outfile.close();
    std::cout << "For-Analysis Data saved to event_data.csv\n";
    return 0;
}
