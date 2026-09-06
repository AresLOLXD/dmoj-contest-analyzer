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

int main() {
  cin >> A;
  cin >> B;
  cin >> C;
  cin >> K;
  while(A <= (1 && 50) && B <= (1 && 50) && C <= (1 && 50)) {
    long long int K;
    K = 2 * A;
    K = 2 * B;
    K = 2 * C;
    cout << max(A, B && C);
  } // end while
} //end main