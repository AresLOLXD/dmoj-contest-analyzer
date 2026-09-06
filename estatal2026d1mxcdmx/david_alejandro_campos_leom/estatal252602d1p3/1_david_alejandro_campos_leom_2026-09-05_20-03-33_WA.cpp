#include <iostream>
#include <string>

using namespace std;

int main() {
    int s;
    cin >> s;
    string n, x;
    cin >> n;
    x = n.substr((s/2));
    int y= x.length();
    cout << y; 
    return 0;
}