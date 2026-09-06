#include <bits/stdc++.h>
using namespace std;

int main() {
    int n;
    string s;

    cin >> n;
    cin >> s;

    int izquierda[26] = {};
    int derecha[26] = {};

    // Al principio, todas las letras están en la derecha
    for (char c : s) {
        derecha[c - 'a']++;
    }

    int comunes = 0;
    int respuesta = 0;

    // Probamos todos los cortes
    for (int i = 0; i < n - 1; i++) {
        int x = s[i] - 'a';

        // Antes de mover la letra, comprobamos si ya estaba
        // en la izquierda y también estaba en la derecha.
        izquierda[x]++;
        derecha[x]--;

        // Si aparece al menos una vez en ambos lados,
        // entonces es una letra común.
        if (izquierda[x] == 1 && derecha[x] > 0) {
            comunes++;
        }

        // Si ya no queda ninguna copia en la derecha,
        // deja de ser una letra común.
        if (derecha[x] == 0 && izquierda[x] > 0) {
            comunes--;
        }

        respuesta = max(respuesta, comunes);
    }

    cout << respuesta << '\n';

    return 0;
}