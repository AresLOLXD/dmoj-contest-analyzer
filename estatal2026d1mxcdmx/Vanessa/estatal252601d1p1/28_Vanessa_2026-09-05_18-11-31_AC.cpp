#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    
    long long a, b, c, k;
    if (!(cin >> a >> b >> c)) return 0;
    cin >> k;

    long long M = max({a, b, c});
    long long sum = a + b + c;

    long long p = 1;
    for (int i = 0; i < k; i++) p *= 2LL;

    long long ans = (sum - M) + M * p;
    cout << ans << "\n";
    return 0;
}