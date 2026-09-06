#include <bits/stdc++.h>
#define ll long long int
using namespace std;
int main() {
    ll n,oeste=0, este=0,suma1=0,alto=0,g=0;
    ll direccion[200002];
    cin>>n;
    for(int c=0; c<n; c++){
        cin>>direccion[c];
        if(direccion[c]==0){
            oeste=oeste+1;
        }else if(direccion[c]==3){
            este=este+1;
    }
    }
    if(oeste ==este){
        cout<<oeste;
        return 0;
    }
    else if(este>oeste){
        cout<<este;
        return 0;
    }
    return 0;
}