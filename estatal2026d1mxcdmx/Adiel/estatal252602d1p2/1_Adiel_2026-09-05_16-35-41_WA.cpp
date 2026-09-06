#include <iostream>
#include <string>
#include <algorithm>
#include <set>
#include <math.h>
#include <numeric>

using namespace std;

// Variables globales

int main() {
    long long int n,o;
    int e=0;
    int a=0;
    int i= 1;
    cin >> n;
    while (i<=n) {
        cin >> o;
        if (o == 0){
            e++;
        } else {
            a++;
        }
        i++;
    }
    if (e>a){
        a=a-1;
        cout << a << endl;
    } else {
        e=e-1;
        cout << e << endl;
    }
    
    return 0;
} //end main