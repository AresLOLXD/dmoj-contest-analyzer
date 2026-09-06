#include <iostream>
#include <vector>
#include <algorithm>

using namespace std;

int main() {
    int N;
    if (!(cin >> N)) return 0;

    vector<int> v(N);
    int personas_a_la_derecha_mirando_este = 0;

    for (int i = 0; i < N; i++) {
        cin >> v[i];
        if (v[i] == 3) {
            personas_a_la_derecha_mirando_este++;
        }
    }

    int personas_a_la_izquierda_mirando_oeste = 0;
    int min_cambios = N + 1;

    for (int i = 0; i < N; i++) {
        if (v[i] == 3) {
            personas_a_la_derecha_mirando_este--;
        }

        int cambios_izquierda = personas_a_la_izquierda_mirando_oeste;
        int cambios_derecha = personas_a_la_derecha_mirando_este;

        int cambios_totales = cambios_izquierda + cambios_derecha;
        min_cambios = min(min_cambios, cambios_totales);

        if (v[i] == 0) {
            personas_a_la_izquierda_mirando_oeste++;
        }
    }

    cout << min_cambios << endl;

    return 0;
}