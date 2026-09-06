#include <iostream>
#include <string>
#include <algorithm>
#include <set>
#include <math.h>
#include <numeric>
using namespace std;
long long int B = 0;
long long int C = 0;
long long int A = 0;
long long int i = 0;
long long int j = 1;
long long int suma = 0;

int main() {
  cin >> A;
  cin >> B;
  cin >> C;
  cin >> i;
  
if (A>B && A>C){
while(j != i) {
    A = A * 2;
    j = j + 1;
  }
}
else if (B>A && B>C){
    while(j != i) {
    B = B * 2;
    j = j + 1;
  }
}
else if (C>A && C>B){
    while(j != i) {
    C = C * 2;
    j = j + 1;
  }
}
else if(A==B && B==C){
    while(j != i) {
    A = A * 2;
    j = j + 1;
  }
}
suma=A+B+C;
cout<<suma<<endl; 
}