#include <bits/stdc++.h>
#include <iostream>
using namespace std;

int main() {
    int n;
    int mult = 0;
    cin >> mult;
    int coso;
    int sum = 0;
    int i = 0;
    int i2 = 0;
    int result = 0;

    while(i <= 3){
        cin >> n;
        if(n > coso){
            coso = coso + n;
        }

        sum = sum + n;
        i++;
    }
    
    while(i2 <= mult){
        result = coso * 2;
        i2++;
    }

    cout << coso + sum;



}