/* --------examen suma mayor------------
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


 -------examen Alineate-------
#include <bits/stdc++.h>
using namespace std;
using ll = long long;
ll arr[200001];
int main(){
    ios_base::sync_with_stdio(0);
    ll n;
    cin>>n;
    ll pasosmaximos=0;
    ll otrospasos=0;
    ll pasosminimos=200001;
    for(ll i = 0; i < n; i++) cin>>arr[i];
    for(ll i = 1; i < n; i++){
        if(arr[i]==3) pasosmaximos++;
    }
    pasosminimos=pasosmaximos;
    for(ll i = 1; i < n; i++){
        if(arr[i-1]==0){
         otrospasos++;
        }
        if(arr[i]==3) pasosmaximos--;
        pasosminimos=min(pasosminimos, pasosmaximos+otrospasos);
    }
    cout<<pasosminimos;
    return 0;
}
*/

#include <bits/stdc++.h>
using namespace std;
using ll = long long;

set<char>izquierda;
set<char>derecha;
int main(){
     ios_base::sync_with_stdio(0);
    ll n;
    cin>>n;
    char aux;
    ll diferentes=0;
    for(ll i = 0; i < n/2; i++){
        cin>>aux;
        izquierda.insert(aux);
    } 
    for(ll i = 0; i <=n/2; i++){
        cin>>aux;
        derecha.insert(aux);
    }
    for(auto c: izquierda){
        if(derecha.count(c) > 0) diferentes++;
    }
    cout<<diferentes/2;
    return 0;
}