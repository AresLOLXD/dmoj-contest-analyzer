// Source: https://usaco.guide/general/io
#include <iostream>
#include <vector>
#include <algorithm>

using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int n;
    if (!(cin >> n)) return 0;

    vector<int> a(n);
    int cambios_actuales = 0;

    for (int i = 0; i < n; i++) {
        cin >> a[i];
    }

    for (int i = 1; i < n; i++) {
        if (a[i] == 1) {
            cambios_actuales++;
        }
    }

    int min_cambios = cambios_actuales;

    for (int i = 1; i < n; i++) {

        if (a[i - 1] == 0) {
            cambios_actuales++;
        }

        if (a[i] == 1) {
            cambios_actuales--;
        }

        min_cambios = min(min_cambios, cambios_actuales);
    }

    cout << min_cambios << "\n";

    return 0;
}