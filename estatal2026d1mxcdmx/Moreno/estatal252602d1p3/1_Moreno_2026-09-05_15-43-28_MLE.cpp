// Source: https://usaco.guide/general/io

#include <bits/stdc++.h>
using namespace std;
#define ll long long

void solve(){
    int n;cin>>n;
    string s;cin>>s;
    vector<vector<bool>> l(n,vector<bool>(26)), r(n,vector<bool>(26));
    l[0][s[0] - 'a'] = true;
    for(int i = 1; i < n; ++i){
        for(int j = 0; j < 26; ++j){
            l[i][j] = l[i - 1][j];
        }
        l[i][s[i] - 'a'] = true;
    }
    r[n - 1][s[n - 1] - 'a'] = true;
    for(int i = n - 2; i >= 0; --i){
        for(int j = 0; j < 26; ++j){
            r[i][j] = r[i + 1][j];
        }
        r[i][s[i] - 'a'] = true;
    }
    int ans = 0;
    for(int i = 0; i < n - 1; ++i){
        int c = 0;
        for(int j = 0; j < 26; ++j){
            if(l[i][j] == r[i + 1][j] && l[i][j] == true)++c;
        }
        ans = max(ans,c);
    }
    cout<<ans<<endl;

    
}

int main() {
    ios_base::sync_with_stdio(0);
    cin.tie(0);
    cout.tie(0);
    solve();
}