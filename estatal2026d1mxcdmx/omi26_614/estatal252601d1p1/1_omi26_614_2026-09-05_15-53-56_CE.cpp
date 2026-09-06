#include <iostream>
#include <algorithm>
using namespace std;

int main() {
    long long A, B, C, 
    int K ;
    cin >> A >> B >> C;
    cin >> k;
    long long mayor = max ({A, B, C});
    long long respuesta = A + B + C - mayor;
 for (int i = 0 ; i < k; i++) {
     mayor += 2;
 }
    cout << respuesta << endl;
    return 0;
}