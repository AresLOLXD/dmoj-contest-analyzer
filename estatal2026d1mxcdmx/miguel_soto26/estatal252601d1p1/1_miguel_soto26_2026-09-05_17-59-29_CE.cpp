#include <iostrean>
#include <algorithm>

using namespace std ;

int main () {
    long long A,B,C,K
    if (!(cin>>A>>B>>C>>K)) return 0;
    
    long long mayor = max ({ A,B,C});
    
    long long suma_otros =A,B,C-mayor ;
    
    long long resultado = mayor * (1LL<<K)) + suma_otros ;
    
    acount<<resultado<<endl ; 
    return 0
    
    }