#include <bits/stdc++.h>
#define ll long long int 
using namespace std;
ll personas=0;
ll direccion[200002]={0};
ll menos =0;
ll total =0;
ll n=0;
ll i = 1;
int main() {
cin>> personas;
for ( int i=1; i <= personas; i++){
cin >> direccion[i];
}
menos = personas/2;

for (int i =1; i <= menos; i++){
if ( direccion[personas] != direccion[menos]){
n++;
}
}

cout << abs(n - 1);
return 0;
}