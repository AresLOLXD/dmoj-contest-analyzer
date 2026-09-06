#include <bits/stdc++.h>
#define ll long long int
using namespace std;
int main() {
    int a,b,c,k;
    ll mayor, sumamenores,r=0;
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
    for(int c=0; c<k; c++){
        r=mayor*2;
        mayor=r;
    }
    cout<<r+sumamenores;
    return 0;
}