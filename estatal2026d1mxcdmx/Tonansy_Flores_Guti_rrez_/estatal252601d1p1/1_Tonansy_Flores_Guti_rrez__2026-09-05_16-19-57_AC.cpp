#include <iostream>
using namespace std;


int main(){
    long long A, B, C;
    int K;
    
    cin >> A >> B >> C >> K;
    long long mayor;
    
    if(A >= B && A>=C){
        mayor=A;
    }
    else if (B >= A && B>=C){
        mayor=B;
    }
    else {
        mayor=C;
    }
    
    for (int i=0; i<K; i++){
        mayor=mayor*2;
    }
    cout <<A + B + C -(mayor/(1LL<< K))+ mayor;
    
return 0;
}