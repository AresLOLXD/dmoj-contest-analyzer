#include <bits/stdc++.h>
#include <boost/multiprecision/cpp_int.hpp>
using namespace std;
using boost::multiprecision::cpp_int;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    
    long long a,b,c;
    long long k;
    if(!(cin >> a >> b >> c)) return 0;
    if(!(cin >> k)) k = 0;

    long long M = max({a,b,c});
    long long sum = a + b + c;

    cpp_int pow2 = cpp_int(1);
    pow2 <<= k; // 2^k

    cpp_int ans = cpp_int(sum - M) + cpp_int(M) * pow2;
    cout << ans << "\n";
    return 0;
}