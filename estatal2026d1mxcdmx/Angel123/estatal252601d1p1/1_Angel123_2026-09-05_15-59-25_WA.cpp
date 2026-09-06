#include <iostream>
#include <string>
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
long long int valormaximo;
long long int i = 0;
long long int l = 0;


int main() {
  cin >> a;
  cin >> b;
  cin >> c;
  cin >> k;
  
  k = c;
    
  l = k * 2;
  i = l + a + b;
  cout << i;
} //end main