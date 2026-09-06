#include <bits/stdc++.h>

using namespace std;

int main() {
long long int a,b,c,n;
cin>>a>>b>>c;
cin>>n;
vector<long long int>dato(3);
dato[0] = a;
dato[1] = b;
dato[2] = c;
sort(dato.begin(), dato.end());
reverse(dato.begin(), dato.end());
for (int i =0 ; i<n; i++){
dato[0] = dato[0]*2; 
}    
cout<<dato[0]+dato[1]+dato[2];   
    
    return 0;
}