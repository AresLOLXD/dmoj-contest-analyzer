#include <bits/stdc++.h>
using namespace std;

int main(){
    unsigned long long int A, B, C, K, mayor;
    //Obtoene los 4 datos al mismo tiempo
    cin>>A>>B>>C>>K;
    //obtiene el mayor de los 3
    mayor=max( max( A, B ), C );
    //se multiplica el numero más grande k veces
    for(int i=0; i < K; i++){
        mayor*=2;
    }
    mayor += ( ( A+B+C ) - max( max( A, B ), C ) );
    cout<<mayor;
}