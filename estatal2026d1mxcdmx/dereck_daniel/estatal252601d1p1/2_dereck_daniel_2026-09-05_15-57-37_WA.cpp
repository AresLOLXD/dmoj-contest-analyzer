#include <bits/stdc++.h>
#define ll long long int
using namespace std;
int main() {
multiset<double>abc;
double a,k=0,ult=1,max=0,r=0;
for(int i=0;i<=2;i++){
    cin>>a;
    abc.insert(a);
}
for(auto x:abc){
    max=x;
}
cin>>k;//cantidad de veces que se puede multiplicar
ult=2*k;//cantidad de veces * 2
r=ult*max;//ingresar el numero multiplicado
for(auto x:abc){
    r+=x;
}
r=r-max;
cout<<r;
}