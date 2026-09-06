#include <iostream>
#include <string>

using namespace std;

int main() {
    int s;
    cin >> s;
    string n, x, y;
    cin >> n;
    x = n.substr(0,(s/2));
    y = n.substr((s/2));
    cout << x<< y; 
    return 0;
}