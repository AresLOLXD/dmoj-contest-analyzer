#include <bits/stdc++.h>
#define ll long long int
using namespace std;
int main() {
multiset<ll>abc;
ll a,k=0,ult=0,max=0,r=0;
for(int i=0;i<=2;i++){
    cin>>a;
    abc.insert(a);
}
for(auto x:abc){
    max=x;
}
cin>>k;//cantidad de veces que se puede multiplicar
ult=max;
while(k>0){
    ult=ult*2;
    k--;
}
r+=ult;
for(auto x:abc){
    r+=x;
}
r=r-max;
cout<<r;
}