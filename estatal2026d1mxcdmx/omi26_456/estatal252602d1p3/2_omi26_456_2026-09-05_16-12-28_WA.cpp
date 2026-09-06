// Source: https://usaco.guide/general/io

#include <bits/stdc++.h>
using namespace std;

int main() {
	int n; 
    char c;
    char caract;

    cin >> n;
    char arr[n] = {};

    for (int i = 0; i < n; i++) {
        cin >> c;
        arr[i] = c;
    }

    int cont = 0;

    caract = arr[0];

    for (int i = 0; i < n; i++) {
        if (arr[i] == caract) {
            cont++;
        }
    }
    if (cont == n) {
        cout << 1;
    }

}