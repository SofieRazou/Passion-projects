#include <opencv2/opencv.hpp>
#include <opencv2/features2d.hpp>
#include <vector>
#include <iostream>
#include <climits>
#include <cmath>
using namespace std;
using namespace cv;

// Edge structure for MST
struct Edge {
    int u, v;
    double weight;
};

// Union-Find (Disjoint Set)
class UnionFind {
    vector<int> parent, size;
public:
    UnionFind(int n) : parent(n), size(n, 1) {
        for (int i = 0; i < n; ++i) parent[i] = i;
    }
    int find(int x) {
        if (parent[x] != x) parent[x] = find(parent[x]);
        return parent[x];
    }
    bool unite(int u, int v) {
        u = find(u); v = find(v);
        if (u == v) return false;
        if (size[u] < size[v]) swap(u, v);
        parent[v] = u;
        size[u] += size[v];
        return true;
    }
};

// Borůvka MST for keypoints
vector<Edge> BoruvkaMST(const vector<Point2f>& points) {
    int n = points.size();
    UnionFind uf(n);
    vector<Edge> edges;

    // Build fully connected graph (keypoints -> edges)
    for (int i = 0; i < n; i++) {
        for (int j = i+1; j < n; j++) {
            double dx = points[i].x - points[j].x;
            double dy = points[i].y - points[j].y;
            double dist = sqrt(dx*dx + dy*dy);
            edges.push_back({i, j, dist});
        }
    }

    int components = n;
    vector<Edge> mst;

    while (components > 1) {
        vector<Edge> cheapest(n, {-1,-1,DBL_MAX});

        // Find cheapest edge for each component
        for (auto &e : edges) {
            int setU = uf.find(e.u);
            int setV = uf.find(e.v);
            if (setU == setV) continue;
            if (e.weight < cheapest[setU].weight) cheapest[setU] = e;
            if (e.weight < cheapest[setV].weight) cheapest[setV] = e;
        }

        // Add edges to MST
        for (auto &e : cheapest) {
            if (e.weight != DBL_MAX && uf.unite(e.u, e.v)) {
                mst.push_back(e);
                components--;
            }
        }
    }
    return mst;
}

int main() {
    VideoCapture cap(0);
    if(!cap.isOpened()) {
        cerr << "Cannot open camera\n";
        return -1;
    }

    Ptr<Feature2D> orb = ORB::create(100); // detect 100 keypoints
    Mat frame, gray;

    while (true) {
        cap >> frame;
        if (frame.empty()) break;

        cvtColor(frame, gray, COLOR_BGR2GRAY);

        // --- Step 1: ORB keypoints
        vector<KeyPoint> keypoints;
        Mat descriptors;
        orb->detectAndCompute(gray, noArray(), keypoints, descriptors);

        // --- Step 2: Build graph from keypoints
        vector<Point2f> points;
        for (auto &kp : keypoints) points.push_back(kp.pt);

        vector<Edge> mst;
        if (points.size() > 1)
            mst = BoruvkaMST(points);

        // --- Step 3: Draw keypoints and MST edges
        Mat output = frame.clone();
        drawKeypoints(frame, keypoints, output, Scalar(0,255,0), DrawMatchesFlags::DEFAULT);

        for (auto &e : mst) {
            Point2f p1 = points[e.u];
            Point2f p2 = points[e.v];
            line(output, p1, p2, Scalar(255,0,0), 1);
        }

        imshow("ORB + Boruvka MST", output);
        if(waitKey(1) == 27) break; // ESC to exit
    }

    cap.release();
    destroyAllWindows();
    return 0;
}
