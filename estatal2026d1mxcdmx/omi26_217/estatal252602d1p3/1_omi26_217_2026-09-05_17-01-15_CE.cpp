// Source: https://usaco.guide/general/io

#include <bits/stdc++.h>
#include <string>
using namespace std;

int main() {
 #include <iostream>
#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <algorithm>

using namespace std;

int main(){
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int n;
    if (!(cin >> n)) return 0;

    string s;
    cin >> s;

    unordered_map<char, int> freq_derecha;
    for (char c : s) {
        freq_derecha[c]++;
    }

    unordered_set<char> visto_izquierda;
    int max_comunes = 0;

    for (int i = 0; i < n - 1; i++) {
        char c = s[i];

        visto_izquierda.insert(c);

        freq_derecha[c]--;
        if (freq_derecha[c] == 0) {
            freq_derecha.erase(c);
        }

        int comunes = 0;
        for (char izq : visto_izquierda) {
            if (freq_derecha.count(izq)) {
                comunes++;
            }
        }

        max_comunes = max(max_comunes, comunes);
    }

    cout << max_comunes << "\n";

    return 0;
}
	
}