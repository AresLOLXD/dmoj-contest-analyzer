#include <bits/stdc++.h>

using namespace std;

int main() {
     int n;
    int mult = 0;
    cin >> mult;
    int op = 0;
    int sum = 0;
    int i = 0;
    int i2 = 0;
    int result = 0;

    while(i <= 3){
        cin >> n;
        if(n > op){
            op = op + n;
        }

        sum = sum + n;
        i++;
    }
    
    while(i2 <= mult){
        result = op * 2;
        i2++;
    }

    cout << op + sum;


    
    
    return 0;
}