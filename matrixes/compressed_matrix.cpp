#include<iostream>
#include<iomanip>
#include<vector>
#include<thread>
#include<mutex>
#include<stdexcept>
#include<climits>
#include<algorithm>
using namespace std;

class Matrix{
    private:
        int n, m;
        vector<vector<int>> matrix;
    public:
        Matrix(int n,int m, int init): n(n), m(m), matrix(n, vector<int>(m, init)) {}
        
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

class CSRMatrix{
        private:
            int n, m;
            vector<int> values;
            vector<int> colIndex;
            vector<int> rowNum;
        public:
            CSRMatrix(int r, int c): n(r), m(c){}
            friend class Matrix;
            int getrows() const {
                int rows = INT_MIN;
                for(int i=0;i<rowNum.size();++i){
                    if(rowNum.at(i)>rows)
                        rows = rowNum.at(i);
                }
                return rows;
            }
            int getcols() const {
                int cols = INT_MIN;
                for(int i=0;i<colIndex.size();++i){
                    if(colIndex.at(i)>cols)
                        cols =colIndex.at(i);
                }
                return cols;
            }

            static CSRMatrix compress(const Matrix &C){
                   CSRMatrix c(0,0,0);
                   for(int i=0;i<C.numRows();++i){
                    for(int j=0;j<C.numCols();++j){
                        if(C(i,j)!=0){
                            c.values.push_back(C(i,j));
                            c.colIndex.push_back(j);
                            c.rowNum.push_back(i);
                        }
                    }
                   }
                   return c;
            }
            static Matrix decompress(const CSRMatrix &c){
                   Matrix C(c.getrows(),c.getcols(), 0);
                   for(int i = 0 ;i< c.n;++i){
                       for(int j=c.rowNum[i];j<c.rowNum(i+1);++j){
                           int col = c.colIndex[j];
                           int val = c.values[j];
                            c(i,col) = val;
                       }  
                }

            }
};

