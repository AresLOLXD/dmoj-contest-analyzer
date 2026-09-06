#include <bits/stdc++.h>
#define ll long long int
using namespace std;
int main() {
    ll n,oeste=0, este=0,suma1=0,suma2=0,suma3=0,alto=0,g=0;
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
    for(int i=1; i<n; i++){
        if(direccion[i]== direccion[0]){
            suma1++;
            suma2--;
            if(suma1>alto){
                alto=suma1;
                g=i;
            }
        } else{
            suma2++;
            suma1--;
         if(suma2>alto){
                alto=suma2;
                g=i;
            }
        }
    }
       if(suma2>suma1){
            for(ll a=g+1; a<n; a++){
            if(direccion[a]== direccion[g]){
                suma3++;
            }
        }
       for(ll a=g-1; a>=0; a--){
           if(direccion[a]!= direccion[g]){
                suma3++;
            }
        }
        cout<<suma3;
    return 0;
}
 if(suma1>suma2){
     for(ll a=g+1; a<n; a++){
            if(direccion[a]== direccion[g]){
                suma3++;
            }
        }
       for(ll a=g-1; a>=0; a--){
           if(direccion[a]!= direccion[g]){
                suma3++;
            }
        }
        cout<<suma3;
    return 0;
}
if(suma1==suma2){
    if(este>oeste){
        cout<<oeste-1;
    }else{
        cout<<este-1;
    }
}
return 0;
}