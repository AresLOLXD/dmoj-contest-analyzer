#include <iostream>
using namespace std;

int main()
{
    
    int A, B, C, X, Y, Z;
    int a, b, c;
    
    cin>>A;
    cin>>B;
    cin>>C;
    
    a = A * 2;
    b = B * 2;
    c = C * 2;
    
    X = a + B + C;
    Y = b + A + C;
    Z = c + A + B;
    
    if (X > Y && X > Z){
        cout<<X;
    }else if(Y > X && Y > Z){
        cout<<Y;
    }else if(Z > X && Z > Y){
        cout<<Z;
    }
    return 0;
}