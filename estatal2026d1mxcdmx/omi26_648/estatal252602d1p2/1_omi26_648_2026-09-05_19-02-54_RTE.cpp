#include <stdio.h>
#include <iostream>
using namespace std;
int main()
{
    int n;
    int gente[100];
    int minimo = 1000000;
    cin >> n;
for (int i=0; i<n; i++){
  cin >> gente[i];
    }
for (int lider=0; lider<n; lider++){
    int cambio = 0;
for (int i=0; i<lider; i++){
    if (gente[i] == 0){
    cambio++;
    }
    }
for (int i=lider+1; i<n; i++){
    if (gente[i] == 3){
 cambio++;
 }
 }
if (cambio < minimo){
    minimo = cambio;
   }
    }
cout << minimo;
 return 0;
}