#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int N;
    if(!(cin >> N)) return 0;
    string S;
    cin >> S;

    while((int)S.size() < N && cin >> ws &&!cin.eof()){
        string extra; cin >> extra;
        S += extra;
    }
    N = S.size();

    vector<int> sufCnt(26,0);
    for(char ch: S) sufCnt[ch-'a']++;

    vector<int> preCnt(26,0);
    int ans = 0;

    for(int i=0; i<N-1; i++){
        int c = S[i]-'a';
        preCnt[c]++;
        sufCnt[c]--;

        int cur = 0;
        for(int k=0;k<26;k++) if(preCnt[k]>0 && sufCnt[k]>0) cur++;
        ans = max(ans, cur);
    }
    cout << ans << "\n";
    return 0;
}