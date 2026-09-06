#include<bits/stdc++.h>

#define ld long double
#define ff first
#define pb push_back 
#define ss second
#define ll long long
#define vi vector<int>
#define vll vector<ll>
#define MAT vector<vll>
#define MAX 100005
#define ull unsigned long long
#define all(x) x.begin(), x.end()
#define sz(x) (int)x.size()
#define pii pair<int,int>
#define MOD 1000000007

using namespace std;

struct Node{
    Node * childs[26] = {nullptr};
    int cnt = 0;
};
void add(Node* Trie, string& word, int idx){
    Trie -> cnt += 1;
    if(sz(word) == idx) return;
    int c = word[idx] - 'a';
    if(!Trie -> childs[c])
        Trie -> childs[c] = new Node;
    add(Trie -> childs[c], word, idx +1);
}

int cnt_pref(Node *Trie, string& query, int idx){
    if(sz(query) == idx) return Trie -> cnt;
    int c = query[idx] - 'a';
    if(!Trie -> childs[c]) return 0;
    return cnt_pref(Trie -> childs[c], query, idx +1);
}

void solve() {
    string s;
    getline(cin, s);
    map<string,int> cnt_word;
    string aux="";
    for(int i = 0; i < sz(s); ++i){
        if(s[i] == ' '){
            if(aux == "") continue;
             cnt_word[aux] += 1;
             aux = "";
        }else
            aux += s[i];
    }
    cnt_word[aux] += 1;
    for(auto &[word, cnt] : cnt_word)
        cout << word << " " << cnt << "\n";
}

int main() {
    cin.tie(0) -> sync_with_stdio(0);
    int t = 1; // cin >> t; 
    while(t--) solve();
    return 0;
}