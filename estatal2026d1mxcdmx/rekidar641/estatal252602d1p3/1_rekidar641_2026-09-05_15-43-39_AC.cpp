#include <bits/stdc++.h>
using namespace std;
#define ll long long
int main() {
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(NULL);
    int n; 
    string s;
    cin >> n >> s;
    int izq[26] = {};
    int der[26] = {};
    for(char c: s){
        der[c-'a']++;
    }
    int r = 0;
    int c = 0;
    for(int i = 0; i < n-1; i++){
        int l = s[i]-'a';
        izq[l]++;
        der[l]--;
        if(izq[l] == 1 && der[l] > 0)
            c++;
        if(der[l] == 0 && izq[l] > 1)
            c--;
        r = max(r,c);
    }
    cout << r;
}