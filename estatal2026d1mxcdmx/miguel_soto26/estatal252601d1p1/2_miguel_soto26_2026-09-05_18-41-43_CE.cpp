#include <iostrean>
#include <algorithm>

using namesapace std ; 

int main () { 
    long long A,B,C,K 
    if ( ! ( cin>>A>>B>>C>>K)) return 0; 
    
    long long mayor = max ({A,B,C});
    long long sumar_otros=A+B+C-mayor; 
    
    long long resultado=mayor *(1LL<<K))+suma otros;
    
    count<<resultado<<endl ;
    return 0 
    
    }