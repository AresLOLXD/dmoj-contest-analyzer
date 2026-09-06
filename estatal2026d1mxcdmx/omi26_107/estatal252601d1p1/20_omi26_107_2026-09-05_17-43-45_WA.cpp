#include <iostream>
using namespace std;
int main() {
int a=0, b=0,c=0;
int k=0;
int i=1;
int v=0;
long long int x=0;
cin >>a>> b>>c >> k;
if ( a > b and a >c){
v = a;
while ( k>= i){
v = v *2;
i++;
}
cout << v + b +c;
return 0;
}
else if ( b > a and b > c){
v = b;
while ( k>= i){
v = v *2;
i++;
}
cout << v + a +c;
return 0;
}
else {
v = c;
while ( k>= i){
v = v *2;
i++;
}
cout << v + b +a;
return 0;
}
 return 0;
}