#include <bits/stdc++.h>

using namespace std;

int main() {
    int N;
    cin >> N;

    int total3 = 0;
    
    int a[200000];

    
    for (int i = 0; i < N; i++) {
        cin >> a[i];

        if (a[i] == 3) {
            total3++;
        }
    }

    int izq0 = 0;
    int mejor = N;

    for (int i = 0; i < N; i++) {

        
        int der3 = total3;

        
        if (a[i] == 3) {
            der3--;
        }

        
        int cambios = izq0 + der3;

        if (cambios < mejor) {
            mejor = cambios;
        }

        
        if (a[i] == 0) {
            izq0++;
        }

        if (a[i] = 3) {
            total3--;
        }
    }

    cout << mejor << endl;

    return 0;
}