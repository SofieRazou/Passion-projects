#include <iostream>
#include <vector>
#include <cmath>
#include <fstream>
#include <ctime>
using namespace std;

struct Point {
    double x, y;
};

double heuristic(Point p1, Point p2) {
    return hypot(p1.x - p2.x, p1.y - p2.y);
}

struct Tree {
    Point val;
    Tree* parent;
    vector<Tree*> neighbours;

    Tree(Point p, Tree* n) : val(p), parent(n) {}
};

Tree* nearest(Tree* root, const Point& target) {
    Tree* best = root;
    double best_dist = heuristic(root->val, target);

    for (Tree* child : root->neighbours) {
        Tree* cur = nearest(child, target);
        double d = heuristic(cur->val, target);
        if (d < best_dist) {
            best = cur;
            best_dist = d;
        }
    }
    return best;
}

Point steer(const Point& start, const Point& end, double delta_t) {
    double dx = end.x - start.x;
    double dy = end.y - start.y;
    double norm = sqrt(dx * dx + dy * dy);

    if (norm == 0.0)
        return start;

    return {
        start.x + delta_t * dx / norm,
        start.y + delta_t * dy / norm
    };
}

Tree* compute_rrt(int k, Point start, double delta_t) {
    Tree* rrt = new Tree(start, nullptr);

    for (int i = 0; i < k; ++i) {
        Point x_rand{
            double(rand() % 100),
            double(rand() % 100)
        };

        Tree* x_near = nearest(rrt, x_rand);
        Point x_new = steer(x_near->val, x_rand, delta_t);

        Tree* node = new Tree(x_new, x_near);
        x_near->neighbours.push_back(node);
    }

    return rrt;
}

void save_edges(Tree* t, ofstream& file) {
    for (Tree* t0 : t->neighbours) {
        file << t->val.x << " " << t->val.y << " "
             << t0->val.x << " " << t0->val.y << "\n";
        save_edges(t0, file);
    }
}

int main() {
    srand(time(nullptr));

    double start_x, start_y;
    cin>>start_x>>start_y;

    Point start{start_x, start_y};
    Tree* rrt = compute_rrt(1000, start, 2.0);

    ofstream file("rrt2d.txt");
    save_edges(rrt, file);
    file.close();

    cout << "2D RRT saved to rrt2d.txt\n";
    return 0;
}
