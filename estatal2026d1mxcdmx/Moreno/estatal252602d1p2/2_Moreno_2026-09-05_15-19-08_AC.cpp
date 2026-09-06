// Source: https://usaco.guide/general/io

#include <bits/stdc++.h>
#include <ios>
using namespace std;
#define ll long long

void solve(){
    int n;cin>>n;
    vector<int> v(n);
    for(auto &x : v)cin>>x;
    vector<int> sum(n);
    int c = 0,maxi = 0;
    for(int i = 0; i < n; ++i){
        if(v[i] == 3)++c;
        sum[i] = c;
    }
    c = 0;
    for(int i = n - 1; i >= 0; --i){
        if(v[i] == 0)++c;
        sum[i] += c;
        maxi = max(maxi,sum[i]);
    }
    cout<<n - maxi<<endl;
    
}

int main() {
    ios_base::sync_with_stdio(0);
    cin.tie(0);
    cout.tie(0);
    solve();
}