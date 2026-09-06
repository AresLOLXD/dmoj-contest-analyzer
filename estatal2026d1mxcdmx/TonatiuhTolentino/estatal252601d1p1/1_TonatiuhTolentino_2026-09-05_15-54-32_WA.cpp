#include <bits/stdc++.h>
using namespace std;

int num[3];
int k = 0;
int a = 0;
int suma = 0;
int mayor = 0;

int main() {
    int i = 0;
    while(i <= 2){
        cin >> num[i];
        //cout << num[i] << "\n";
        i++;
    }
    cin >> k;
    //cout << k << endl;

    int n = 0;
    while(n < 3){
        a = num[n];

        i = 0;
        while(i < k){
            a = a * 2;
            i++;
        }


        if(n == 0){
            suma = a + num[1] + num[2];
        }
        else{
            if(n == 1){
                suma = a + num[0] + num[3];
            }
            else{
                if(n == 2){
                    suma = a + num[0] + num[1];
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