#include <bits/stdc++.h>
using namespace std;
using ll = long long;
ll numeros[4];
int main(){
    ios_base::sync_with_stdio(0);
    cin.tie(0);
    cout.tie(0);
    cin>>numeros[0];
    cin>>numeros[1];
    cin>>numeros[2];
    ll n;
    cin>>n;
    sort(numeros, numeros+3);
    for(ll i = 1; i <= n; i++ ) numeros[2]*=2;
    cout<<numeros[2]+numeros[1]+numeros[0];
    return 0;
}