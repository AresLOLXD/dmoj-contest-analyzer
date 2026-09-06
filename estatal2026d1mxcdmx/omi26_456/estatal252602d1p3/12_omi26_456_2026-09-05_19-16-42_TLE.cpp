// Source: https://usaco.guide/general/io

#include <bits/stdc++.h>
using namespace std;

int main() {
	int n; 
    int maximus = 0;
    string s;
    
    cin >> n;
    cin >> s;

    for (int i = 0; i < n; i++) {
        set<char> x;
        set<char> y;

        // Valores únicos
        for (int j = 0; j < i; j++) {
            x.insert(s[j]);
        }

        for (int k = i; k < n; k++) {
            y.insert(s[k]);
        }

        int enAmbos = 0;
        

        // Comprobar si están en ambos set
        for (char c : x) {
            // comprobar si es unico
            if (y.find(c) != y.end()) {
                enAmbos++;
            } 
            maximus = max(maximus, enAmbos);
        }
        
    }
    cout << maximus;
}