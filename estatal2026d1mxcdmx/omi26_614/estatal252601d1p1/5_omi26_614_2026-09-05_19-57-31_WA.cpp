#include <iostream>
using namespace std;

int main() {
    int a, b, c, k;
    cin >> a >> b >> c;
    cin >> k;

    for (int i = 0; i < k; i++) {
        if (a <= b && a <= c) {
            a *= 2;
        } else if (b <= a && b <= c) {
            b *= 2;
        } else {
            c *= 2;
        }
    }

    cout << a + b + c << '\n';
    return 0;
}