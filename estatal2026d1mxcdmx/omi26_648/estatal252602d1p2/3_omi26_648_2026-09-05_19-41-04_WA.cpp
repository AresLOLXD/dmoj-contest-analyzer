#include <stdio.h>
#include <iostream>
using namespace std;
int main()
{
 int izq = 0;
int der = 0;
int n;
int gente [200000];
 int minimo = 1000000;
cin >> n;
for (int i = 0; i < n; i++){
    if (gente[i] == 3){
        der++;
    }
}

for (int lider = 0; lider < n; lider++){

    if (gente[lider] == 3){
        der--;
    }

    int cambio = izq + der;

    if (cambio < minimo){
        minimo = cambio;
    }

    if (gente[lider] == 0){
        izq++;
    }
}
cout << minimo;
 return 0;
}