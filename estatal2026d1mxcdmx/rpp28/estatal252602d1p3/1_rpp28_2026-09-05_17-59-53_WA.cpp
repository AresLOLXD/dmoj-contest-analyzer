#include <bits/stdc++.h>
#define ll long long int
using namespace std;
ll n, com, mayor;
string cadena;
set <char> der;
multiset<char>derecha;
set<char>izq;

int main() {
    ios_base::sync_with_stdio; cin.tie(); cout.tie();
    cin>>n>>cadena;
    for (auto x: cadena){
        derecha.insert(x);
        der.insert(x);
    }
    if(der.size()==1){
        cout<< 1;
        return 0;
    }
    for (auto x: cadena){
        if(der.contains(x)){
            derecha.find(derecha.erase(x));
            if(derecha.contains(x)){
                izq.insert(x);
            } else {
                der.erase(x);
                izq.erase(x);
            } 
        }
        com=der.size()+izq.size();
        mayor=max(mayor, com);
    }
    cout<<mayor;
}