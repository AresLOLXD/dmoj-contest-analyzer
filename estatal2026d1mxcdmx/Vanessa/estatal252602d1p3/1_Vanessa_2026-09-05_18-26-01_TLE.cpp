#include <bits/stdc++.h>
using namespace std;
int main(){
    int n; string s;
    cin >> n >> s;
    int ans = 0;
    for(int i=1;i<n;i++){
        bool a[26]={}, b[26]={};
        for(int j=0;j<i;j++) a[s[j]-'a']=1;
        for(int j=i;j<n;j++) b[s[j]-'a']=1;
        int cur=0;
        for(int k=0;k<26;k++) if(a[k]&&b[k]) cur++;
        ans = max(ans,cur);
    }
    cout<<ans;
}