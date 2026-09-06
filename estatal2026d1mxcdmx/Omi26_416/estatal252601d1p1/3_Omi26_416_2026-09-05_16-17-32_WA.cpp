#include <iostream>
#include <string>
#include <algorithm>
#include <set>
#include <math.h>
#include <numeric>

using namespace std;

// Variables globales
long long int A = 0;
long long int B = 0;
long long int C = 0;
long long int K = 0;
long long int multi = 0;
long long int suma = 0;
long long int i = 0;

int main() {
  cin >> A;
  cin >> B;
  cin >> C;
  cin >> K;
  i = 1;
  if(i != K) {
    while(i < K) {
      if(A > (B && C)) {
        multi = A *2 + A * 2;
        suma = B + C;
        i = i + 1;
      } //end if
      if(B > (A && C)) {
        multi = B * 2 + B * 2;
        suma = A + C;
        i = i + 1;
        if(C > (A && B)) {
            cout << "prueba ";
          multi = C * 2 + C * 2;;
          suma = A + B;
          i = i + 1;
        } //end if
      } //end if
    } // end while
  } //end if
  else {
     if(A > (B && C)) {
      multi = A * 2;
      suma = B + C;
    } //end if
    if(B > (A && C)) {
      multi = B * 2;
      suma = A + C;
    } //end if
    if(C > (A && B)) {
      multi = C * 2;
      suma = A + B;
    } //end if
  } //end else
  K = multi + suma;
  cout << K;
  return 0;
} //end main