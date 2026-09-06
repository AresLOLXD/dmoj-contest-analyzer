#include <bits/stdc++.h>
using namespace std;

int numero[4];
int k = 0;
int a = 0;
int suma = 0;
int mayor = 0;

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
        else{
            if(n == 1){
                suma = a + numero[0] + numero[3];
            }
            else{
                if(n == 2){
                    suma = a + numero[0] + numero[1];
                }
            }
        }

        if(suma > mayor){
            mayor = suma;
        }
        
    n++;
    }
    cout << mayor << "\n";
}