#include <iostream>
#include <algorithm> 

using namespace std;

int main() {
   
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    long long a, b, c;
    int k;

    if (cin >> a >> b >> c >> k) {
        
        long long maximo = max({a, b, c});
        
        long long suma_total = a + b + c;
        
        long long maxima_suma_posible = (suma_total - maximo) + (maximo << k);
        
       
        cout << maxima_suma_posible << "\n";
    }

    return 0;
}