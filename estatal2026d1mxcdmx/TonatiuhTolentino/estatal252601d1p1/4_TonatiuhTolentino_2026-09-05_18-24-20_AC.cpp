#include <bits/stdc++.h>
using namespace std;

long long int numero[4];
long long int k = 0;
long long int a = 0;
long long int suma = 0;
long long int mayor = 0;

int main() {
    int i = 0;
    while(i <= 2){
        cin >> numero[i];
        //cout << num[i] << "\n";
        i++;
    }
    cin >> k;
    //cout << k << endl;

    int n = 0;
    while(n < 3){
        a = numero[n];

        i = 0;
        while(i < k){
            a = a * 2;
            i++;
        }


        if(n == 0){
            suma = a + numero[1] + numero[2];
        }
        if(n == 1){
            suma = numero[0] + a + numero[2];
        }
        if(n == 2){
            suma = numero[0] + numero[1] + a;
        }

        if(suma > mayor && suma != 0){
            mayor = suma;
        }
        
    n++;
    }
    cout << mayor;
}