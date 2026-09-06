#include <iostream>
using namespace std;

int main() {
    long long a, b, c, n;
    cin >> a >> b >> c >> n;

    long long mayor = max(a, max(b, c));

    while (n > 0) {
        mayor *= 2;
        n--;
    }

    cout << a + b + c - max(a, max(b, c)) + mayor << endl;

    return 0;
}