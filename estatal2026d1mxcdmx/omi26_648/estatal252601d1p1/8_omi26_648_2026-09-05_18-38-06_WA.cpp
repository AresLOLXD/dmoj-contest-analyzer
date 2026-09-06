#include <stdio.h>
#include <iostream>
using namespace std;
int main()
{
int A;
int B;
int C;
int K;
int S;

cin >> A >> B >> C;
cin >> K;

if (A > B && A > C){
   S = A;
    for (int i=1; i<=K; i++){
    S = S * 2;}
 cout << S + B + C; }
 
   else if (B > A && B > C){
       S = B;
       for (int i=1; i<=K; i++){
           S = S * 2;
       }
     cout << S + A +C;
   }
    else if  (C > B && C > A){
        S = C;
        for ( int i= 0; i<=K; i++){
            S = S * 2;
        }
    cout << S+ A + B;
}

 return 0;
}