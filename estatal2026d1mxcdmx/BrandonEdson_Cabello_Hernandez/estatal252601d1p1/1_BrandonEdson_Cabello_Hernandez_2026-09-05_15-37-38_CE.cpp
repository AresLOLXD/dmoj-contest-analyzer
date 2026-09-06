#include <bits/stdc++.h>

using namespace std;

int main() {
    
    long long a,b,c,k;
    cin >> a >> b >> c >> k
    
    long long mx = max(a, max(b,c));
    long long resto = a + b + c - mx
    
    long long base =2;
    long long c + b = k;
    usingned long long pot = 1
    while (exp > 0){
        if (exp & 1) pot * = base;
    base = base;
    exp >> = 1;
    }
    usingned long long resultado = resto + mx * pot;
    cout resultado << endl
    return 0;
}