#include <bits/stdc++.h>
using namespace std;
int main() {
int a, b,c;
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
return 0;
} 
if (x > v and z ){
cout << x;
return 0;
}
if ( z> v and x){
cout << z;
return 0;
}
 return 0;
}