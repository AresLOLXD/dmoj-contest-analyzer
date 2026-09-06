#include <bits/stdc++.h>
#define ll long long int
using namespace std;
int main() {
    ll a,b,c,k;
    ll mayor, sumamenores ,r=0;
    cin>>a>>b>>c>>k;
    if(a>b && a>c){
        mayor=a;
        sumamenores=b+c;
    }
    else if(b>a && b>c){
        mayor=b;
        sumamenores=a+c;
    }
    else if(c>a && c>b){
        mayor=c;
        sumamenores= a+b;
    }
    else if(a==b && a==c){
        mayor=a;
        sumamenores=a+a;
    }
    for(int i=0; i<k; i++){
        r=mayor*2;
        mayor=r;
    }
    r=r+sumamenores;
    cout<<r;
    return 0;
}