#include <bits/stdc++.h>
using namespace std;

int main(){
    int n, acomodo=0, minimo=200000;
    cin>>n;
    int areglo[n];
    for(int i=0; i < n; i++){
        cin>>areglo[i];
    }

        //revisa todo el areglo una vez
    for( int j=1; j < n; j++){

        if (areglo[j] == 3){
            acomodo++;
        }     

    }

    minimo = min(minimo, acomodo);
    for(int i=1; i < n; i++){
        if(areglo[i] == 3){
            acomodo--;
        }
        if(areglo[i-1] == 0){
            acomodo++;
        }
        minimo = min(minimo, acomodo);
    }
        
    cout<<minimo;
     return 0;
}