#include <iostream>
#include <string>
#include <algorithm>
#include <set>
#include <math.h>
#include <numeric>

using namespace std;

// Variables globales
long long int oeste = 0;
long long int este = 3;
long long int N;

int main() {
  cin >> oeste;
  cin >> este;
  cin >> N;
  if(oeste < este) {
    N /= oeste;
  } //end if
  cout << endl;
  if(oeste == este) {
    N -= oeste;
  } //end if
  cout << endl;
  return 0;
} //end main