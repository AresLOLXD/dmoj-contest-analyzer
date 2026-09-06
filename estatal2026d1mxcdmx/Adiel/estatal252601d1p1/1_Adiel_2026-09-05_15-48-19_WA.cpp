#include <iostream>
#include <string>
#include <algorithm>
#include <set>
#include <math.h>
#include <numeric>

using namespace std;

// Variables globales

int main() {
    int a,b,c,k,o_a,o_b,o_c,valormax1,valormax2;
    int i = 1;
    cin >> a ;
    cin >> b ;
    cin >> c ;
    cin >> k ;
    o_a= a;
    o_b =b;
    o_c =c;
    while (i<=k) {
      a=a*2;
      b=b*2;
      c=c*2;
     i++;
    }
    a=a+o_b+o_c;
    b=b+o_a+o_c;
    c=c+o_b+o_a;
    valormax1 = max(a,b);
    valormax2 = max(b,c);
    if (valormax2 == valormax1) {
        cout << b << endl;
    }
    else {
        cout << max(a,c) << endl;
    }
    
    return 0;
} //end main