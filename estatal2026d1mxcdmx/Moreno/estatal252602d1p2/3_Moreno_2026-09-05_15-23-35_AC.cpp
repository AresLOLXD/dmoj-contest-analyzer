// Source: https://usaco.guide/general/io

#include <bits/stdc++.h>
#include <ios>
using namespace std;
#define ll long long

void solve(){
    int n;cin>>n;
    vector<int> v(n);
    for(auto &x : v)cin>>x;
    vector<int> l(n),r(n);
    for(int i = 1; i < n; ++i){
        l[i] = l[i - 1] + (v[i - 1] == 3 ? 1 : 0);
    }
    for(int i = n - 2; i >= 0; --i){
        r[i] = r[i + 1] + (v[i + 1] == 0 ? 1 : 0);
    }
    int ans = n;
    for(int i = 0; i < n; ++i){
        ans = min(ans, n - l[i] - r[i]);
    }
    cout<<ans - 1<<endl;
    
}

int main() {
    ios_base::sync_with_stdio(0);
    cin.tie(0);
    cout.tie(0);
    solve();
}