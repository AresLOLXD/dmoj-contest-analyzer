#include <iostream>
using namespace std;

int main()
{
    
    int A, B, C, X, Y, Z;
    int a, b, c;
    int K;
    
    cin>>A;
    cin>>B;
    cin>>C;
    cin>>K;
    
    a = A * K;
    b = B * K;
    c = C * K;
    
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