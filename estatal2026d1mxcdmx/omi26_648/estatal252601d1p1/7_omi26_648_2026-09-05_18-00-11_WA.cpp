#include <stdio.h>
#include <iostream>
using namespace std;
int main()
{
int A;
int B;
int C;
int K;


cin >> A >> B >> C;
cin >> K;

if (A > B && A > C){
    
    cout <<   (A * 2 * K) + B + C; 
}
   else if (B > A && B > C){
     cout << (B * 2 * K) + A + C;
   }
    else if  (C > B && C > A){
    cout << (C * 2 * K) + A + B;
}

 return 0;
}