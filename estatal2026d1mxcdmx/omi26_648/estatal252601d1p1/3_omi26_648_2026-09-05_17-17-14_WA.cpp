#include <stdio.h>
#include <iostream>
using namespace std;
int main()
{
int A;
int B;
int C;
int K;
int a;
int b; 
int c;
cin >> A >> B >> C;
cin >> K;
for (int i=1; i<=K; i++){
if (A > B && C){
    cout << (A * 2) + B + C;
}
    else if (B > A && C){
     cout << (B * 2) + A + C;
}
    else if (C > B && A){
    cout << (C * 2) + A + B;
}
}
 return 0;
}