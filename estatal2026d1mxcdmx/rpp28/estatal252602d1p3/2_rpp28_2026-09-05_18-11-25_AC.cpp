#include <bits/stdc++.h>
#define ll long long int
using namespace std;
ll n, com, mayor;
string cadena;
set <char> der;
multiset<char>derecha;
set<char>izq;

int main() {
    cin>>n>>cadena;
    for (auto x: cadena){
        derecha.insert(x);
        der.insert(x);
    }
    if(der.size()==1){
        cout<< 1;
        return 0;
    }
    der.clear();

    for (auto x: cadena){
        if(derecha.contains(x)){
            derecha.erase(derecha.find(x));
            if(derecha.contains(x)){
                der.insert(x);
                izq.insert(x);
            } else {
                der.erase(x);
                izq.erase(x);
            } 
        }
        com=der.size();
        mayor=max(mayor, com);
    }
    cout<<mayor;
}