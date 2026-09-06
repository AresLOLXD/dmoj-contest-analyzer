#include <iostream>
#include <string>
#include <vector>
#include <algorithm>

using namespace std;

int main() {
    // Optimización de E/S
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int n;
    if (!(cin >> n)) return 0;

    string s;
    cin >> s;

    // Frecuencias de letras a la derecha (Y)
    vector<int> count_derecha(26, 0);
    for (char c : s) {
        count_derecha[c - 'a']++;
    }

    // Presencia de letras a la izquierda (X)
    vector<bool> esta_izquierda(26, false);

    int max_coincidencias = 0;

    // Probamos cortar en cada posición de izquierda a derecha
    // (el corte ocurre justo después de s[i])
    for (int i = 0; i < n - 1; i++) {
        int idx = s[i] - 'a';
        
        // El carácter actual pasa a estar a la izquierda (X)
        esta_izquierda[idx] = true;
        
        // Y deja de estar en la derecha (Y)
        count_derecha[idx]--;

        // Contamos cuántas letras están en ambos lados
        int coincidencias_actuales = 0;
        for (int c = 0; c < 26; c++) {
            if (esta_izquierda[c] && count_derecha[c] > 0) {
                coincidencias_actuales++;
            }
        }

        max_coincidencias = max(max_coincidencias, coincidencias_actuales);
    }

    cout << max_coincidencias << "\n";

    return 0;
}