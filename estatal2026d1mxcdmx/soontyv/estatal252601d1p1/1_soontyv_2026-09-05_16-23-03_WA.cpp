#include <iostream>
using namespace std;

int main() {

	int A,B,C;
    cin>>A>>B>>C;
    int k;
    cin>>k;
    int Ra=0, Rb=0, Rc=0;
    int sumaA=0, sumaB=0, sumaC=0;
    int sumaMayor=0;
    for(int i=0; i<k; i++){
        Ra=A*2;
        sumaA=Ra+B+C;
        Rb=B*2;
        sumaB=Rb+A+C;
        Rc=C*2;
        sumaC=Rc+A+B;
    }
    if( sumaA > sumaB && sumaC ){
        sumaMayor=sumaA;
    }else if( sumaB > sumaA && sumaC ){
        sumaMayor=sumaB;
    }else if( sumaC > sumaA && sumaB ){
        sumaMayor=sumaC;
    }
    cout<<sumaMayor;
    

	return 0;
}