#include <bits/stdc++.h>

using namespace std;

int main() {
	  long A, B, C;
    int K;
    
    if (cin >> A >> B >> C >> K) {
       
        long long max_val = max({A, B, C});
        
        
        long long resto = (A + B + C) - max_val;
        
       
        long long max_transformado = max_val * (1LL << K);
        
        cout << resto + max_transformado << endl;
    }
    
    return 0;
}