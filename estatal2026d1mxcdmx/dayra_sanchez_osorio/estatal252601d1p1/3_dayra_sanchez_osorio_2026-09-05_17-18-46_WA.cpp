#include <bits/stdc++.h>
using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(nullptr);

    int a, b ,c, k;
    cin >> a >> b >> c >> k;
    int mejor = max(a ,b);
    mejor = (mejor, c);
    long long mejorx =  mejor;
    // << mejor << "\n";
    for(int i=0;i<k;i++){
        mejorx = mejorx * 2;
    }
    // << mejorx << "\n";

    long long suma = a + b + c + mejorx - mejor;

    cout << suma;

    return 0;
}