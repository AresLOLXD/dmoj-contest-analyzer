#include <stdio.h>
#include <iostream>
using namespace std;
int main()
{
int A;
int B;
int C;
int mayor;
int n;
cin >> A >> B >> C;
cin >> n;
if (A >B && C){
    cout << (A * n) + B + C;
}
    else if (B > A && C){
    cout << (B * n) + A + C;
    }
    else if (C > B && A){
    cout << (C * n) + A + B;
}

    return 0;
}