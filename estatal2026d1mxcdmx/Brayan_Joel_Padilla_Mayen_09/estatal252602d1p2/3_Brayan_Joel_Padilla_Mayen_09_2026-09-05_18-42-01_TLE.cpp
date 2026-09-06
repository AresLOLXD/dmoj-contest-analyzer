#include <bits/stdc++.h>
using namespace std;

int main() {
    int n;
    cin >> n;

    vector<int> a(n);
    for (int &x : a) cin >> x;

    int ans = n;

    for (int leader = 0; leader < n; leader++) {
        int changes = 0;

        // Personas a la izquierda: deben mirar al este (3)
        for (int i = 0; i < leader; i++) {
            if (a[i] != 3)
                changes++;
        }

        // Personas a la derecha: deben mirar al oeste (0)
        for (int i = leader + 1; i < n; i++) {
            if (a[i] != 0)
                changes++;
        }

        ans = min(ans, changes);
    }

    cout << ans << '\n';

    return 0;
}