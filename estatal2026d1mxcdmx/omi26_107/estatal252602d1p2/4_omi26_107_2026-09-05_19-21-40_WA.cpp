#include <bits/stdc++.h>
#define ll long long int 
using namespace std;
ll personas=0;
ll direccion[200002]={0};
ll menos =0;
ll total =0;
ll n = 0;
int main() {
cin>> personas;
for(int i=1; i<=personas; i++){
cin>> direccion[i];
}
for (int i=1; i <= personas; i++){
if (direccion[i] != direccion[i+1]){
menos ++;
personas--;
}
}
cout << menos - 1;
return 0;
}