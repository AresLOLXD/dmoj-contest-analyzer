// Source: https://usaco.guide/general/io

#include <bits/stdc++.h>
using namespace std;

int main() {

	// int cont = 0;
    int n; 
    string car;
    string x;
    string y;
    set<char> xUnico;
    set<char> yUnico;
    set<char> unicos;

    cin >> n;
    cin >> car; 

    for (int i = 0; i < n; i++) {
        if (i < n / 2) {
            x += car[i];
        }
        else {
            y += car[i];
        }
    }

    // agregar caracteres a set 
    for (char c : x) {
        xUnico.insert(c);
    }
    for (char c : y) {
        yUnico.insert(c);
    }

    for (char c : x) {
        // comprobar si es unico
        if (yUnico.find(c) != yUnico.end()) {
            unicos.insert(c);
        } 
    }
    for (char c : y) {
        // comprobar si es unico
        if (xUnico.find(c) != xUnico.end()) {
            unicos.insert(c);
        } 
    }

    if (yUnico.size() == 1 && xUnico.size() == 1){
        cout << 1;
    }   
    else {
        cout << unicos.size();
    }

    
}