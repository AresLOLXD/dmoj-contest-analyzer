#include <iostream>
#include <string>
#include <algorithm>
#include <set>
#include <math.h>
#include <numeric>

using namespace std;

// Variables globales
long long int N = 0;
string S = "";

int main() {
  while(2 <= (N <= 200000)) {
    cin >> N;
    cin >> S;
  } // end while
  cout << max(N, S);
} //end main