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
S=K*2;
if (A > B && A > C){
    cout << (A * S) + B + C;
}
   else if (B > A && B > C){
     cout << (B * S) + A + C;
   }
    else if  (C > B && C > A){
    cout << (C * S) + A + B;
}
 return 0;
}#include <stdio.h>
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
S=K*2;
if (A > B && A > C){
    cout << (A * S) + B + C;
}
   else if (B > A && B > C){
     cout << (B * S) + A + C;
   }
    else if  (C > B && C > A){
    cout << (C * S) + A + B;
}
 return 0;
}