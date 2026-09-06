#include <algorithm>
#include <set>
#include <math.h>
#include <numeric>

using namespace std;

// Variables globales
long long int a = 0;
long long int b = 0;
long long int c = 0;
long long int k = 0;
long long int maxi = 0;

int main() {
  cin >> a;
  cin >> b;
  cin >> c;
  cin >> k;
  if(a > b) {
    if(b < c) {
      if(c > a) {
        k = b * 2;
        maxi = k + a + c;
      } //end if
    } //end if
  } //end if
} //end main