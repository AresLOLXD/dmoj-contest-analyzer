#include <bits/stdc++.h>
using namespace std;
int main()
{
    int n= 0;
    cin>>n;
    int arreglo[200001]={};
    for(int i=1; i<=n;i++){
        cin>>arreglo[i];
    }
    cout<<n/2-1;
}