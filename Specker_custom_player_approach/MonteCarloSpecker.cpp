#include <iostream>
#include <string>
#include <vector>
#include <stdexcept>
#include <cstdlib>

// --- Move class ---
class Move {
public:
    Move(unsigned int source, unsigned int source_coins, unsigned int target, unsigned int target_coins)
        : source(source), source_coins(source_coins), target(target), target_coins(target_coins) {}

    unsigned int getSource() const { return source; }
    unsigned int getSourceCoins() const { return source_coins; }
    unsigned int getTarget() const { return target; }
    unsigned int getTargetCoins() const { return target_coins; }

    std::string getDescription() const {
        return "takes " + std::to_string(source_coins) + " coins from heap " +
               std::to_string(source) + " and puts " + std::to_string(target_coins) +
               " coins to heap " + std::to_string(target);
    }

private:
    unsigned int source;
    unsigned int source_coins;
    unsigned int target;
    unsigned int target_coins;
};

// --- State class ---
class State {
public:
    State(unsigned int heaps) : heaps(std::vector<unsigned int>(heaps, 0)), playing(0) {}

    void addCoins(unsigned int heap, unsigned int coins) {
        if (heap >= heaps.size()) throw std::invalid_argument("Invalid heap index");
        heaps[heap] += coins;
    }

    void next(const Move& move) {
        if (move.getSource() >= heaps.size() || move.getTarget() >= heaps.size())
            throw std::invalid_argument("Invalid heap index in move");
        if (move.getSource() == move.getTarget())
            throw std::invalid_argument("Source and target heaps must be different");
        if (heaps[move.getSource()] < move.getSourceCoins())
            throw std::invalid_argument("Not enough coins in source heap");

        heaps[move.getSource()] -= move.getSourceCoins();
        heaps[move.getTarget()] += move.getTargetCoins();
        playing = (playing + 1) % 2;
    }

    bool winning() const {
        for (unsigned int c : heaps) if (c > 0) return false;
        return true;
    }

    unsigned int getCoins(unsigned int heap) const {
        if (heap >= heaps.size()) throw std::invalid_argument("Invalid heap index");
        return heaps[heap];
    }

    unsigned int getHeaps() const { return heaps.size(); }
    unsigned int getPlaying() const { return playing; }

    std::string getState() const {
        std::string s;
        for (unsigned int i = 0; i < heaps.size(); ++i) {
            s += std::to_string(heaps[i]);
            if (i + 1 < heaps.size()) s += ", ";
        }
        return s + " with " + std::to_string(playing) + "/2 playing next";
    }

private:
    std::vector<unsigned int> heaps;
    unsigned int playing;
};

// --- Player base class ---
class Player {
public:
    Player(std::string name) : name(name) {}
    virtual ~Player() {}
    virtual const Move play(const State& s) = 0;
    std::string getName() const { return name; }
    virtual std::string getType() const = 0;

private:
    std::string name;
};

// --- GreedyPlayer ---
class GreedyPlayer : public Player {
public:
    GreedyPlayer(std::string name) : Player(name) {}
    const Move play(const State& s) override {
        unsigned int max_coins = 0, from = 0;
        for (unsigned int i = 0; i < s.getHeaps(); ++i) {
            if (s.getCoins(i) > max_coins) {
                max_coins = s.getCoins(i);
                from = i;
            }
        }
        for (unsigned int i = 0; i < s.getHeaps(); ++i) {
            if (i != from)
                return Move(from, max_coins, i, max_coins - 1);
        }
        throw std::runtime_error("No legal moves available");
    }
    std::string getType() const override { return "Greedy"; }
};

// --- MonteCarloPlayer ---
class pi24b597 : public Player {
public:
    pi24b597(std::string name) : Player(name) {}
    const Move play(const State& s) override {
        std::vector<Move> legal;
        for (unsigned int from = 0; from < s.getHeaps(); ++from) {
            unsigned int coins = s.getCoins(from);
            if (coins >= 1) {
                for (unsigned int take = 1; take <= coins; ++take) {
                    for (unsigned int to = 0; to < s.getHeaps(); ++to) {
                        if (from == to) continue;
                        for (unsigned int put = 0; put < take; ++put)
                            legal.emplace_back(from, take, to, put);
                    }
                }
            }
        }
        if (legal.empty()) throw std::runtime_error("No legal moves available");
        return legal[rand() % legal.size()];
    }
    std::string getType() const override { return "Monte_Carlo"; }
};

// --- Game class ---
class Game {
public:
    Game(unsigned int heaps, unsigned int players)
        : num_heaps(heaps), num_players(players),
          state(new State(heaps)), players() {}

    ~Game() {
        delete state;
        for (Player* p : players)
            delete p;
    }

    void addHeap(unsigned int heap, unsigned int coins) {
        state->addCoins(heap, coins);
    }

    void addPlayer(Player* player) {
        if (players.size() >= num_players)
            throw std::runtime_error("Too many players");
        players.push_back(player);
    }

    void play() {
        while (!state->winning()) {
            std::cout << "State: " << state->getState() << std::endl;
            Player* p = players[state->getPlaying()];
            Move m = p->play(*state);
            std::cout << p->getType() << " player " << p->getName() << " "
                      << m.getDescription() << std::endl;
            state->next(m);
        }
        std::cout << "State: " << state->getState() << std::endl;
        std::cout << players[state->getPlaying()]->getName() << " wins" << std::endl;
    }

private:
    unsigned int num_heaps;
    unsigned int num_players;
    State* state;
    std::vector<Player*> players;
};

// --- Main example ---
int main() {
    srand(time(0)); // Set a seed for reproducibility

    Game game(3, 2);
    game.addHeap(0, 10);
    game.addHeap(1, 15);
    game.addHeap(2, 20);

    game.addPlayer(new GreedyPlayer("Alice"));
    game.addPlayer(new pi24b597("Bob"));
    
    game.play();

    return 0;
}
