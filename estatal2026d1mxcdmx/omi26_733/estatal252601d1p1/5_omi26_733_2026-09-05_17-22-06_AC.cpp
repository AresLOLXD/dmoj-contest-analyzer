#include <iostream>
#include <algorithm>

using namespace std;

int main() {
    // Optimización de entrada y salida
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    long long a, b, c, k;
    if (cin >> a >> b >> c >> k) {
        // 1. Identificamos el número más grande
        long long mayor = max({a, b, c});
        
        // 2. Calculamos la suma de los otros dos números
        long long suma_resto = (a + b + c) - mayor;

        // 3. Multiplicamos de manera segura en un bucle
        // Esto evita el undefined behavior de (1LL << k) cuando k >= 63
        while (k > 0 && mayor < (1LL << 62)) {
            mayor *= 2;
            k--;
        }

        // 4. Imprimimos el resultado final
        cout << suma_resto + mayor << "\n";
    }

    return 0;
}