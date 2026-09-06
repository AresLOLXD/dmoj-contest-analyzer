// Source: https://usaco.guide/general/io

#include <bits/stdc++.h>
using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector <int> v(n+1);

    for(int i=1;i<=n;i++){
        int a;
        cin >> a;
        v[i] = a + v[i-1];
    }

    int mejor = 1e6;
    for(int i=1; i<=n;i++){
        int este = (v[n]-v[i])/3;
        int l = v[i-1]/3;
        int oeste = i - l - 1;
        int suma = oeste + este;
        //cout << oeste << ' ' << este << ' ' << suma <<"\n";
        mejor = min(mejor, suma);
    }

    cout << mejor;

    return 0;
}