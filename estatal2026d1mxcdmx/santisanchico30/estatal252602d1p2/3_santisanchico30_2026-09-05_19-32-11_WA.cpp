#include <bits/stdc++.h>
using namespace std;
int main()
{
    long long int n= 0;
    long long int cceros= 0;
    cin>>n;
    long long int arreglo[200001];
    for(int i= 1; i<=n; i++){
        cin>>arreglo[i];
        
    }
    for(int i=1; i<=n; i++){
        if(arreglo[i]==0){
            cceros++;
        }
    }
    cout<<n-cceros;
}