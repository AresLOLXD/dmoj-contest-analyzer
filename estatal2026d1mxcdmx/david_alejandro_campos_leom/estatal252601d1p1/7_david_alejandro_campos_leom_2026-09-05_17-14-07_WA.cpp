#include <iostream>

using namespace std;

int main() {
    int a,b,c,k, ar, br, cr;
    cin >> a >> b >> c;
    cin >> k;
    ar = ((a * 2)* k) + b + c;
    br = ((b * 2)* k) + a + c;
    cr = ((c * 2)* k) + b + a;
    if (ar > br && ar > cr) {
        cout << ar;
    } else if (br > cr) {
        cout << br;
    } else {
        cout << cr;
    }
} //end main