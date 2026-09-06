#include <iostream>
#include <algorithm>
#include <cmath>
using namespace std;

int main() {

    long long a, b, c;
    int k;

if(cin >> a >> b >> c >> k)
{long long max_val = max({a, b, c});
long long suma_otros = (a + b + c) - max_val;

//multiplicar el numero mas grande por 2^k 
long long resultado = (max_val * (1ll << k)) + suma_otros;
cout <<resultado<< endl;




}
    return 0;
}