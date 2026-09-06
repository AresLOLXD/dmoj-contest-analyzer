// Source: https://usaco.guide/general/io

#include <bits/stdc++.h>
using namespace std;
#define ll long long

void solve(){
    int n;cin>>n;
    string s;cin>>s;
    vector<int> l(26),r(26);
    for(int i = 1; i < n; ++i){
        r[s[i] - 'a']++;
    }
    int ans = 0;
    for(int i = 0; i < n - 1; ++i){
        l[s[i] - 'a']++;
        int c = 0;
        for(int j = 0; j < 26; ++j){
            if(l[j] > 0 && r[j] > 0)++c;
        }
        ans = max(ans,c);
        r[s[i + 1] - 'a']--;
    }
    cout<<ans<<endl;
    
}

int main() {
    ios_base::sync_with_stdio(0);
    cin.tie(0);
    cout.tie(0);
    solve();
}