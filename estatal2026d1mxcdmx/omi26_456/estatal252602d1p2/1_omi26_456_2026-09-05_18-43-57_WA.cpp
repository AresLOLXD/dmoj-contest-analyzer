#include <bits/stdc++.h>
using namespace std;

int main() {
    int n, dir;
    int oeste = 0;
    int este = 0;

    cin >> n;

    int minimo = n;

    vector<int> a;

    // Guardar dirección
    for (int i = 0; i < n; i++) {
        cin >> dir;
        a.push_back(dir);
    }
    

    // Contar este
    for (int i = 0; i < n; i++) {
        if (a[i] == 3) {
            este++;
        }
    }

    

    // Probar cada persona como el líder
    for (int i = 0; i < n; i++) {

        // No lo contamos si es lider
        if (a[i] == 3) {
            este--;
        }

        if (a[i] == 0) {
            oeste++;
        }

        int seguidores = oeste + este;
        
        minimo = min(minimo, seguidores);
    }

    cout << minimo;
}