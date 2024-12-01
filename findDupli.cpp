#include<iostream>
using namespace std;

bool FindDupli (int a[], int b[], int N) {
    bool same = false;
    bool found[N];
    for(int k=0;k<N;k++)
        found[k] = false;
    for(int i=0;i<N;i++) {
        if(found[i]==false && a[i] == b[i]) {
            found[i] = true;
            same = true;
        }
    }
    return same;
}

int main() {
    int A[100];
    int B[100];
    int N=0;
    cout<<"Enter the dimention of the two arrays:\n";
    cin>>N;
    cout<<"Enter the array elements:\n";
    for(int i=0;i<N;i++)
        cin>>A[i];
    cout<<"Enter the array elements:\n";
    for(int i=0;i<N;i++)
        cin>>B[i];
    bool same = FindDupli(A, B, N);
    if(same==true)
        cout<<"Yes";
    else
        cout<<"No";
    return 0;
}
