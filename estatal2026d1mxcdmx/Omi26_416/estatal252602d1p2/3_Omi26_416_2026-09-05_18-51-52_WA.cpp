#include <iostream>
#include <string>
#include <algorithm>
#include <set>
#include <math.h>
#include <numeric>

using namespace std;

// Variables globales
long long int N = 0;
long long int num[200002] = {};
long long int i = 0;
long long int oeste = 0;
long long int este = 0;
long long int minimo = 0;
long long int numeros = 0;

int main() {
  cin >> N;
  i = 1;
  while(i <= N) {
    cin >> num[numeros];
    if(num[numeros] == 0) {
      oeste = oeste + 1;
    } //end if
    else {
       este = este + 1;
    } //end else
    i = i + 1;
  } // end while
  if(oeste < este) {
    minimo = oeste - 1;
  } //end if
  else {
     minimo = este - 1;
  } //end else
  cout << minimo;
  return 0;
} //end main