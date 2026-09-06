#include <bits/stdc++.h>
using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(nullptr);

    vector <int> v(3);
    int mejor = 0;

    for(int i=0;i<3;i++){
        int a;
        cin >> a;
        v[i] = a;
        mejor = max(a, mejor);
    }

    int k;
    cin >> k;
    long long mejorx = mejor;
    for(int i=0;i<k;i++){
        mejorx *= 2;
    }

    long long suma = v[0] + v[1] + v[2] + mejorx - mejor;

    cout << suma;

    return 0;
}