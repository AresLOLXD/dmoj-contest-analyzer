#include <bits/stdc++.h>

#include <iostream>
using namespace std;
int main() {
long long int a=0;
long long int b=0;
long long int c=0;
int k=0;
int i=1;
long long int v=0;
cin >>a>> b>>c >> k;
if ( a > b and a >c){
while ( k>= i){
a = a *2;
k--;
}
cout << a + b+ c;
return 0;
}
else if ( b > a and b > c){
while ( k>= i){
b = b *2;
k--;
}
cout << b + a +c;
return 0;
}
else if ( c> a and c >b) {
while ( k>= i){
c = c *2;
k--;
}
cout << c + b +a;
return 0;
}
 return 0;
}