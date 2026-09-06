#include <iostream>

using namespace std;

int main() {
    int a,b,c,k,lg,l2,l3,kc;
    cin>>a>>b>>c;
    cin>>k;
    kc=k;
    if (a<=50&&b<=50&&c<=50&&k<=30&&1<=a&&1<=b&&1<=c&&1<=k) {
    if (a>b&&a>c) {
        lg=a; l2=b; l3=c;
    } else if (b>c) {
        lg=b; l2=a; l3=c;
    } else {
        lg=c; l2=b; l3=a;
    }
    while (kc > 0) {
        lg=lg*2;
        kc--;
    }
    cout << lg + l2 + l3;
    }
    else {
        return 0;
    }
} //end main