#include <iostream>
using namespace std;
int main() {
int a=0, b=0,c=0;
int k=0;
int v=0;
int x=0;
int z=0;
cin >>a>> b>>c >> k;
k=k*2;
v = (k* a) + b+c;
x = (k*b) + a+c;
z= (k*c) + b +a;
if ( v > x and v> z){
cout << v;
 }else if (x > v and x > z ){
cout << x;
 }
if ( z> v and z > x){
cout << z;

}
 return 0;
}