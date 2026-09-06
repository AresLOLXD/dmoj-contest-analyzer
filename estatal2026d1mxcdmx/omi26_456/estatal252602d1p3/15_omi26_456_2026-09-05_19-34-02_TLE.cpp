#include <bits/stdc++.h>
using namespace std;

int main() {
    int n;
    int maximus = 0;
    string s;

    cin >> n;
    cin >> s;

    set<char> x;
    // Tomar incluso repetidos
    multiset<char> y;

    
    for (int i = 0; i < n; i++) {
        y.insert(s[i]);
    }

    for (int i = 0; i < n - 1; i++) {

        
        x.insert(s[i]);

        
        y.erase(y.find(s[i]));

        int enAmbos = 0;

        // Buscar en ambos 
        for (char c : x) {
            if (y.find(c) != y.end()) {
                enAmbos++;
            }
        }

        maximus = max(maximus, enAmbos);
    }

    cout << maximus;
}