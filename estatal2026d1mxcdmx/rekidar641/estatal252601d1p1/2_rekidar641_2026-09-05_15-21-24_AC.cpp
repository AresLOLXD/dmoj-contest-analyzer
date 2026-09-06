#include <bits/stdc++.h>
using namespace std;
#define ll long long
int main() {
    ll a, b, c, k;
    cin >> a >> b >> c >> k;
    while(k--){
        if(a>=b && a >=c)
            a*=2;
        else if(b >= a && b >= c)
            b*=2;
        else
            c*=2;
    }
    cout << a+b+c;
}