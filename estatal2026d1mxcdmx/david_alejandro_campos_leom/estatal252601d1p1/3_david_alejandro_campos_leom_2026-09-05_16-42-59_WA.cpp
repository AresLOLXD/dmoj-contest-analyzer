#include <iostream>

using namespace std;
int main() {
    int a,b,c,k,lg,l2,l3;
    cin >> a >> b >> c; cin >> k;
    if (a > b && a > c) {
        lg = a; l2 = b; l3 = c;
    } else if (b > c) {
        lg = b; l2 = a; l3 = c;
    } else {
        lg = c; l2 = b; l3 = a;
    }
    cout << ((lg * 2)* k) + l2 + l3;
} //end main