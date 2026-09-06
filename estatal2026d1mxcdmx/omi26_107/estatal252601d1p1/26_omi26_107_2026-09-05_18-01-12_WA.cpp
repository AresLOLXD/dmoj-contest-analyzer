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
v = a;
while ( k>= i){
v = v *2;
k--;
}
cout << abs(v + b +c);
return 0;
}
else if ( b > a and b > c){
v = b;
while ( k>= i){
v = v *2;
k--;
}
cout << abs(v + a +c);
return 0;
}
else {
v = c;
while ( k>= i){
v = v *2;
i++;
}
cout << abs(v + b +a);
return 0;
}
 return 0;
}