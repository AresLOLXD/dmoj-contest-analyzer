#include <bits/stdc++.h>
using namespace std;
int main()
{
    long long int n= 0;
    long long int contador=0;
    cin>>n;
    long long int arreglo[200001];
    for(int i= 1; i<=n; i++){
        cin>>arreglo[i];
        
    }
    for(int i=1; i<=n; i++){
        if(arreglo[i]=!arreglo[i-1]){
            contador++;
        }
    }
    cout<<contador;
}