#include <iostream>
#include <algorithm>
using namespace std;

int main() {
    long long  A, B, C 
    int k;
    
    cin >> A >> B >> C;
    cin >> k;
    
    lon long mayor  = max({A, B, C});
    long long respuesta = A + B + C -
    mayor;
    
    for in (int i = 0; i  < k ; i++) {
        mayor += 2;
    }
    cout << respuestas << endl;
    
    return 0;
}