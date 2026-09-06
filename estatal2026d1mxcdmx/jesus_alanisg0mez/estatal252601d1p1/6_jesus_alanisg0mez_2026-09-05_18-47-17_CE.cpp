#include <bits/stdc++.h>
using namespace std;

int main() {
	int a, b, c; 
    if (!(cin >> a >> b >> c)) return 0
	cout << "The sum of these three numbers is " << a + b + c << "\n";
    if (a == b && c) {
        cout << "All are equal\n";
    } else if (b >= a && b >= c) {
        cout b << " is the greatest\n";
    } else if ( a >= b && a >= c) {
        cout a << " is the greatest\n";
    } else {
        cout c <<" is the greatest\n";
    }

    cout << "multiplication is "<< a * b * c <<\n";


    return 0; 


}