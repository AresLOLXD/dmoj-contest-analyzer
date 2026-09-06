#include <bits/stdc++.h>
using namespace std;
int main() {
int a, b,c;
int suma =0;
int mm=0;
int k=0;
int v;
int x;
int z;
cin >>a>> b>>c >> k;
v = (k*2)* a + b+c;
x = (k*2)* b + a+c;
z= (k*2)* c + b+a;
if ( v > x and z){
cout << v;
} 
if (x > v and z ){
cout << x;
}
if ( z> v and x){
cout << z;
}
 return 0;
}