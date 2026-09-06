#include <bits/stdc++.h>
using namespace std;
using ll = long long;
ll arr[4];
int main(){
    ios_base::sync_with_stdio(0);
    ll n;
    cin>>n;
    ll pasosmaximos=0;
    ll otrospasos=0;
    ll pasosminimos=200001;
    for(ll i = 0; i < n; i++){
        cin>>arr[i];
        if(arr[i]==3) pasosmaximos++;
    }
    pasosmaximos--;
    pasosminimos=pasosmaximos;
    for(ll i = 1; i < n; i++){
        if(arr[i-1]==0){
         otrospasos++;
        }
        if(arr[i]==3) pasosmaximos--;
        pasosminimos=min(pasosminimos, pasosmaximos+otrospasos);
    }
    cout<<pasosminimos+1;
    return 0;
}