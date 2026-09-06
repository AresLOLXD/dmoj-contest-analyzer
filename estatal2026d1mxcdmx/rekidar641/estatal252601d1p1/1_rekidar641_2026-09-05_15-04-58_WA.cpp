#include <bits/stdc++.h>
using namespace std;

int main() {
    int a, b, c, k;
    cin >> a >> b >> c >> k;
    int m = max({a,b,c});
    int mm = m*(pow(2,k));
    int sum=0;
    m == a ? a=0:a=a;
    m == b ? b=0:b=b;
    m == c ? c=0:c=c;
    sum+=a; sum+=b; sum+=c; sum+=mm;
    cout << sum;
}