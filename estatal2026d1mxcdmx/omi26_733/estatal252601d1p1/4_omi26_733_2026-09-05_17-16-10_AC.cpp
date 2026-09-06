#include <bits/stdc++.h>
#include <cmath>

using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    long long a, b, c, k;
    if (cin >> a >> b >> c >> k) {
        long long mayor = max({a, b, c});
        long long suma_resto = (a + b + c) - mayor;

        long long mayor_multiplicado = mayor * (1LL << k); // Funciona si k <= 62

        cout << suma_resto + mayor_multiplicado << "\n";
    }

    return 0;
}