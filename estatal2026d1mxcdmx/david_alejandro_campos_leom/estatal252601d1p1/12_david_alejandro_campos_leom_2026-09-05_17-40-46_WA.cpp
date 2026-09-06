#include <iostream>

using namespace std;

int main() {
    int a,b,c,k,ar,br,cr;
    //solicita a,b y c
    cin>>a>>b>>c;
    //solicita k
    cin>>k;
    // ejecuta todos los casos posibles
    ar=((a*2)*k)+b+c;
    br=((b*2)*k)+a+c;
    cr=((c*2)*k)+b+a;
    // analiza que resultado es mayor y lo imprime
    if (ar>br&&ar>cr) {
        cout<<ar;
    } else if (br>cr) {
        cout<<br;
    } else {
        cout<<cr;
    }
}