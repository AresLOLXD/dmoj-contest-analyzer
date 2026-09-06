#include <bits/stdc++.h>
using namespace std;

int main(){
    int n, acomodo=0, minimo=200000;
    cin>>n;
    int areglo[n];
    for(int i=0; i < n; i++){
        cin>>areglo[i];
    }

    //revisa todos los lideres
    for(int i=0; i < n; i++){

        //revisa todo el areglo por cada uno
        for( int j=0; j < n; j++){
            //si estan a la izquierda del lider
            if( j < i){
                if ( areglo[j] == 0 ){
                    //Estan viendo a donde no deberian
                    acomodo++;
                }
            } else if(j > i){

                if (areglo[j] == 3){
                    acomodo++;
                }
            }
        }
        minimo = min(minimo, acomodo);
        acomodo=0;
        
    }
    cout<<minimo;
     return 0;
}