# Heap Game Simulation

Simulates a two-player game between a Greedy player and a Monte Carlo player. The logic behind the Monte Carlo simulation lies in  the random seed which implements the probabilistic algorithm of Monte Carlo, suitable for these types of games, highly scalable. 

If you want to view the accumulative result of monte carlo vs greedy player game, run the specker_mc.cpp file and then the python script specker_stats.py (uses panda library) in order to get the stats of a fair share of games. 

If you wanna run it for one play, run the one_specker_mc.cpp file. Enjoy!

## How to Compile

```bash
g++ -std=c++17 -o  specker_mc.cpp

-- Made by Σοφία Ράζου (el24013), (pi24b597)
