#include <bits/stdc++.h>
#define ll long long int
using namespace std;
int main() {
    ll n,oeste=0, este=0,suma=1,alto=0,g=0;
    ll direccion[200002];
    cin>>n;
    for(int c=0; c<n; c++){
        cin>>direccion[c];
        if(direccion[c]==0){
            oeste++;
        }else if(direccion[c]==3){
            este++;
    }
    }

   if(oeste ==este){
        cout<<oeste;
        return 0;
    }
    for(int i=1; i<n; i++){
        if(direccion[i]== direccion[i-1]){
            suma++;
            if(suma>alto){
                alto=suma;
                g=i;
            }
        }
    }
    suma=0;
    for(ll a=g+1; a<n; a++){
        if(direccion[a]== direccion[a+1]){
            suma++;
        }
    }
     for(ll a=g-1; a>=0; a--){
        if(direccion[a]!= direccion[a+1]){
            suma++;
        }
    }

    return 0;
}

  /*  else if(oeste>este){
        cout<<este;
        return 0;
        }
        else if(este>oeste){
            cout<<oeste;
            return 0;
        }
        */