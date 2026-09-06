#include <bits/stdc++.h>
#define ll long long int
using namespace std;
int main() {
    ll n,oeste=0, este=0;
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
    else if(este>oeste){
        if(direccion[n-1]==este){
        cout<<oeste;
        return 0;
        }
    }else{
         cout<<oeste-1;
        return 0;
    }
    return 0;
}