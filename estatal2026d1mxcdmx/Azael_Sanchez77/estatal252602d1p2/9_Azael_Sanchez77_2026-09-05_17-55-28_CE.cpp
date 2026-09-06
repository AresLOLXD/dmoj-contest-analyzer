#include <bits/stdc++.h>

using namespace std;

int main() {
    return 0;
}#include <bits/stdc++.h>
#define ll long long int
using namespace std;
int main() {
    ll n,oeste=0, este=0,suma=1,alto=0,g=0;
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
            suma++;
            if(suma>alto){
                alto=suma;
                g=i;
            }
        } else{
            suma--;
        }
    }
       suma=0;
        for(int a=g; a<n; a++){
            if(direccion[a]== direccion[g]){
                suma++;
            }
        }
       for(int a=g; a>=0; a--){
           if(direccion[a]== direccion[g]){
                suma++;
            }
        }
        cout<<suma-3;
    return 0;
}