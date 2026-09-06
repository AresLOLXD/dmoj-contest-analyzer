#include <bits/stdc++.h>
#define ll long long int
using namespace std;
ll izq, der, total, n;
ll direc[200002];

int main() {
    cin>>n;
    for (ll i=1; i<=n; i++){
        cin>>direc[i];
            if(direc[i]==3){
                der++;
            }
    }
    total=der;
    for(ll i=1; i<=n; i++){
        if (direc[i]==3){
            der--;
        }
        if(direc[i-1]==0 && i>=2){
            izq++;
        }

        total=min(total, der+izq);
    }
    cout << total;
}