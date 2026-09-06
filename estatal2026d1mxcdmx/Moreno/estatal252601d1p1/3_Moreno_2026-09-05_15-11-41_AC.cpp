// Source: https://usaco.guide/general/io

#include <bits/stdc++.h>
#include <ios>
using namespace std;
#define ll long long

void solve(){
    ll a,b,c;cin>>a>>b>>c;
    if(a > b)swap(a,b);
    if(b > c)swap(b,c);
    ll pp;cin>>pp;
    while(pp--){
        c *= 2;
    }
    cout<<a + b + c;
}

int main() {
    ios_base::sync_with_stdio(0);
    cin.tie(0);
    cout.tie(0);
    solve();
}