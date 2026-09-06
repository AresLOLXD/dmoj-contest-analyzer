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

    int mayor = max(xUnico.size(), yUnico.size());

    if (yUnico.size() == 1 && xUnico.size() == 1){
        cout << 1;
    }
    else {
        cout << mayor;
    }

}