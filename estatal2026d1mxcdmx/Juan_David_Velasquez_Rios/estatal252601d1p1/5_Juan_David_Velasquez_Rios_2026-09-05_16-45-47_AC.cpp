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
long long int j = 0;
long long int suma = 0;

int main() {
  cin >> A>> B>> C>> i;
  
  long long int mayor= max ({A,B,C});
  while (i != j){
      mayor=mayor*2;
      j=j+1;
  }
  cout<<A+B+C+mayor-max ({A,B,C});
}