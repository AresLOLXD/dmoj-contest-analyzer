#include <bits/stdc++.h>

using namespace std;

int main () {
    long long A, B, C;
    int k;
    
    cin >> A >> B >> C >> k;
    
    for (int i=0;i<k; i++){
    if (A>=B && B >= C)
    A *=2;
    if (B>=A && B>= C)
    B *=2;
    else
    C *=2;
    }
    cout << A+B+C<< '\n';
   return 0;
}