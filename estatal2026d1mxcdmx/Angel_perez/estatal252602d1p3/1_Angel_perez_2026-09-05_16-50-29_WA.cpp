#include <bits/stdc++.h>
using namespace std;
using ll = long long;

set<char>arr;
int main(){
     ios_base::sync_with_stdio(0);
    ll n;
    cin>>n;
    char aux;
    ll pasosmaximos=0;
    ll otrospasos=0;
    ll pasosminimos=200001;
    for(ll i = 0; i < n; i++){
        cin>>aux;
        arr.insert(aux);
    } 
    cout<<arr.size();
    
    return 0;
}