#include <bits/stdc++.h>

using namespace std;

int main() {
    // Optimización de lectura y escritura
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    long long a, b, c, k;
    if (cin >> a >> b >> c >> k) {
        // Buscamos el mayor de los tres números
        long long mayor = max({a, b, c});
        
        // Calculamos la suma de los dos números menores
        long long suma_resto = (a + b + c) - mayor;
        
        // Multiplicamos el mayor por 2 a la K (usando bitshift 1LL << k)
        long long mayor_multiplicado = mayor << k;
        
        // Imprimimos la suma total máxima
        cout << suma_resto + mayor_multiplicado << "\n";
    }

    return 0;
}