#include <iostream>
using namespace std;
int main() {
long long int a=0, b=0,c=0;
long long int k=0;
long long int v=0;
cin >>a>> b>>c >> k;
k=k*2;
if ( a > b and a >c){
v = (k *a)+b+c;
}
else if ( b > a and b > c){
v = (k *b)+a+c;
}
else {
v = (k *c)+b+a;
}
cout << v;
 return 0;
}