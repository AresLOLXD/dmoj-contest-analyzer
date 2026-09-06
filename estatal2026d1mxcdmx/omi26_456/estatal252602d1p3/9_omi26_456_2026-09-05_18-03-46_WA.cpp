// Source: https://usaco.guide/general/io

#include <bits/stdc++.h>
using namespace std;

int main() {
	int n; 
    char c;
    string y, x;
    set<char> xUnicos;
    set<char> yUnicos;
    set<char> unicos;

    cin >> n;

    for (int i = 0; i < n; i++) {
        cin >> c;
        if (i < n / 2) {
            x += c;
        }
        else {
            y += c;
        }
    }


    // Valores únicos
    // quitar cout
    for (char j : x){
        xUnicos.insert(j);
    }
    for (char h : y){
        yUnicos.insert(h);
    }


    // Comprobar si están en ambos set
    for (char s : xUnicos) {
        // comprobar si es unico
        if (yUnicos.find(s) != yUnicos.end()) {
            unicos.insert(s);
        } 
    }

    for (char a : yUnicos) {
        // comprobar si es unico
        if (xUnicos.find(a) != xUnicos.end()) {
            unicos.insert(a);
        } 
    }
    if (yUnicos.size() == 1 && xUnicos.size() == 1){
        cout << 1;
    }   
    else {
        cout << unicos.size();
    }
}