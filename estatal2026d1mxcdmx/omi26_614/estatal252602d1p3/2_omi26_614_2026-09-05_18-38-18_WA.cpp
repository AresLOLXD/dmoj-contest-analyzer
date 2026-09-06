#include <iostream>
#include <string>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    string s;
    cin >> n >> s;

    int total[26] = {0};
    for (char c : s) {
        total[c - 'a']++;
    }

    bool izq[26] = {false};
    int maximo = 0;
    int cant_izq = 0;

    // Recorremos HASTA el penúltimo carácter
    for (int i = 0; i < n - 1; i++) {
        int idx = s[i] - 'a';

        // Agregamos la letra a la izquierda
        if (!izq[idx]) {
            izq[idx] = true;
            cant_izq++;
        }

        // La quitamos de la derecha
        total[idx]--;

        // Contamos letras distintas en la derecha
        int cant_der = 0;
        for (int j = 0; j < 26; j++) {
            if (total[j] > 0) cant_der++;
        }

        // Actualizamos el máximo
        if (cant_izq + cant_der > maximo) {
            maximo = cant_izq + cant_der;
        }
    }

    cout << maximo << '\n';
    return 0;
}