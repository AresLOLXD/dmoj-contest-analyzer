#include <iostream>
using namespace std;

int main()
{
    int a, b, c, A, B, C;
    int X, Y, Z;
    int K;
    
    cin>>A;
    cin>>B;
    cin>>C;
    cin>>K;
    
    a = A;
    b = B;
    c = C;
    
    while(K > 0){
        a = a * 2;
        b = b * 2;
        c = c * 2;
        K--;
    }
  
  X = a + B + C;
  Y = A + b + C;
  Z = A + B + c;
  
  if(X > Y && X > Z){
      cout<<X;
  }else if(Y > X && Y > Z){
      cout<<Y;
  }else if(Z > X && Z > Y){
      cout<<Z;
  }
  
    

    return 0;
}