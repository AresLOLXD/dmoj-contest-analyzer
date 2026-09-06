#include <iostream>
#include <vector>
#include <algorithm>

using namespace std;

int main() {
    // Optimización de entrada / salida
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int n;
    if (!(cin >> n)) return 0;

    vector<int> a(n);
    for (int i = 0; i < n; i++) {
        cin >> a[i];
    }

    // prefijo_ceros[i] = cantidad de '0's estrictamente antes del índice i
    vector<int> prefijo_ceros(n, 0);
    for (int i = 1; i < n; i++) {
        prefijo_ceros[i] = prefijo_ceros[i - 1] + (a[i - 1] == 0 ? 1 : 0);
    }

    // sufijo_treses[i] = cantidad de '3's estrictamente después del índice i
    vector<int> sufijo_treses(n, 0);
    for (int i = n - 2; i >= 0; i--) {
        sufijo_treses[i] = sufijo_treses[i + 1] + (a[i + 1] == 3 ? 1 : 0);
    }

    // Evaluamos el costo para cada posible líder y nos quedamos con el mínimo
    int min_cambios = n;
    for (int i = 0; i < n; i++) {
        int cambios = prefijo_ceros[i] + sufijo_treses[i];
        min_cambios = min(min_cambios, cambios);
    }

    cout << min_cambios << "\n";

    return 0;
}