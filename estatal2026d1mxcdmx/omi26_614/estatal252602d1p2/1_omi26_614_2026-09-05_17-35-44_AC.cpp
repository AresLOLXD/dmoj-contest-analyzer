#include <iostream>
using namespace std;

int main() {
    int N;
    cin >> N;

    int personas[200000];

    int tres = 0;

    for (int i = 0; i < N; i++) {
        cin >> personas[i];

        if (personas[i] == 3) {
            tres++;
        }
    }

    int cambios = tres;
    int cerosIzquierda = 0;
    int tresDerecha = tres;

    for (int lider = 0; lider < N; lider++) {

        if (personas[lider] == 3) {
            tresDerecha--;
        }

        int actual = cerosIzquierda + tresDerecha;

        if (actual < cambios) {
            cambios = actual;
        }

        if (personas[lider] == 0) {
            cerosIzquierda++;
        }
    }

    cout << cambios << endl;

    return 0;
}