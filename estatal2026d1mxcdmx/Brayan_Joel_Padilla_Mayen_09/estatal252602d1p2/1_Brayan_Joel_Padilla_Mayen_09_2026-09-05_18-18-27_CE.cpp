includ
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