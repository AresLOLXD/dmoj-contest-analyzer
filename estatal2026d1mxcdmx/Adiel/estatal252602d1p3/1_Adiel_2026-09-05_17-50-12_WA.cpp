#include <iostream>
#include <string>
#include <algorithm>
#include <set>
#include <math.h>
#include <numeric>

using namespace std;

// Variables globales

int main() {
    int i= 1;
    string n= "";
    long long int original=0;
    long long int cad=0;
    long long int dif=0;
    string X="";
    string Y="";
    cin >>  cad;
    cin >> n;
    original=cad;
    cad=cad/2;
    X= n.substr(0,cad);
    cad=cad+1;
    Y= n.substr(cad,original);
    cad=cad-1;
    while(i<=cad){
        if (X.find("a",cad) == Y.rfind("a",0)){
        dif++;
        }
        i++;
    }
    dif--;
    cout << dif <<endl;      
    
    return 0;
} //end main