#include<iostream>
#include<iomanip>
#include<vector>
#include<thread>
#include<mutex>
#include<stdexcept>
using namespace std;

class Matrix{
    private:
        int n, m;
        vector<vector<int>> matrix;
    public:
        Matrix(int n,int m): n(n), m(m), matrix(n, vector<int>(m)) {}


        int numRows() const {return n;}
        int numCols() const {return m;}

        int & operator ()(int i, int j){ return matrix[i][j];}
        int operator()(int i, int j) const {return matrix[i][j];}

       static Matrix multiply(const Matrix &A, const Matrix &B, int t = std::thread::hardware_concurrency()){
            if(A.m != B.n)
                throw invalid_argument("Incompatible matrix sizes for matrix multiplication\n");

            t = std::min(t, A.numRows());

            Matrix C(A.n, B.m);

            auto worker = [&](int row_start, int row_end){
                for(int i = row_start; i < row_end; ++i){
                    for(int j = 0; j < B.m; j++){
                        for(int k = 0; k < A.m; ++k)
                            C(i, j) += A(i, k) * B(k, j);
                    }
                }
            };

            vector<thread> ts;
            ts.reserve(t);

            int rows_per_thread = A.numRows() / t;

            for(int i=0;i<t;++i){
                int start = i*rows_per_thread;
                int end = (i==t-1)? A.numRows(): start + rows_per_thread;
                ts.emplace_back(worker, start, end);
            }

            for(auto &th: ts){
                th.join();
            }

            return C;
}

        void print(){
             for(auto &row: matrix){
                for( auto& val:row)
                     cout<<val<<" ";
                cout<<endl;
             }
        }

};

int main(){
    Matrix A(4,4);
    Matrix B(4,3);
    int v;
    for(int i=0;i<A.numRows();++i){
        for(int j=0;j<A.numCols();++j){
            cin>>v;
            A(i, j) = v;
        }
    }
    for(int i=0;i<B.numRows();++i){
        for(int j=0;j<B.numCols();++j){
            cin>>v;
            B(i, j) = v;
        }
    }
    Matrix C = Matrix::multiply(A,B);
    C.print();
    return 0;
}
