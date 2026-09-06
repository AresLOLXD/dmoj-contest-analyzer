#include <iostream>
#include <string>
#include <vector>
#include <algorithm>

using namespace std;

int main() {
    // Optimización para entrada/salida rápida
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int N;
    if (!(cin >> N)) return 0;

    string S;
    cin >> S;

    // Arreglos de frecuencia para el lado izquierdo (X) y derecho (Y)
    vector<int> freq_izq(26, 0);
    vector<int> freq_der(26, 0);

    // Al inicio, toda la cadena está en el lado derecho Y
    for (char c : S) {
        freq_der[c - 'a']++;
    }

    int max_coincidencias = 0;

    // Probamos mover el corte carácter por carácter de izquierda a derecha
    for (int i = 0; i < N - 1; i++) {
        int char_idx = S[i] - 'a';

        // Pasamos el carácter actual del lado derecho al izquierdo
        freq_izq[char_idx]++;
        freq_der[char_idx]--;

        // Contamos cuántas letras están en ambos lados
        int coincidencias_actuales = 0;
        for (int j = 0; j < 26; j++) {
            if (freq_izq[j] > 0 && freq_der[j] > 0) {
                coincidencias_actuales++;
            }
        }

        max_coincidencias = max(max_coincidencias, coincidencias_actuales);
    }

    cout << max_coincidencias << "\n";

    return 0;
}