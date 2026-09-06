// Source: https://usaco.guide/general/io

#include <bits/stdc++.h>
using namespace std;
#define ll long long

void solve(){
    vector<ll> v(3);
    for(auto &x : v)cin>>x;
    sort(v.begin(),v.end());
    ll c;cin>>c;
    cout<<v[0] + v[1] + (v[2] << c)<<endl;
}

int main() {
    ios_base::sync_with_stdio(0);
    cin.tie(0);
    cout.tie(0);
    solve();
}