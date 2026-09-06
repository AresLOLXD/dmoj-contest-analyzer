#include <bits/stdc++.h>

using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    long long a, b, c, k;
    if (cin >> a >> b >> c >> k) {
        long long mayor = max({a, b, c});
        long long suma_resto = (a + b + c) - mayor;

        // Multiplicamos paso a paso k veces
        while (k > 0) {
            mayor *= 2;
            k--;
        }

        cout << suma_resto + mayor << "\n";
    }

    return 0;
}