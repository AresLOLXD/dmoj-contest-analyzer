#include <iostream>
#include <string>
#include <algorithm>
#include <set>
#include <math.h>
#include <numeric>

using namespace std;

int main (){
    long long int linea [200000]={},num_personas {0}, i{0},volteos_b{0}, volteos_a{0},vm{0};
    cin>>num_personas;
while(num_personas!=i){
cin>>linea[i];
if(linea[i]==3){
volteos_b++;
}
i++;    
}
if (linea[0]==3){
    volteos_b--;
}
vm=volteos_b+volteos_a;
i=1;
while (i != num_personas){
    if (linea[i-1]==0){
        volteos_a++;
    }
     if (linea[i]==3){
        volteos_b--;
    }
    if (volteos_a+volteos_b<vm){
        vm=volteos_b+volteos_a;
    }
    i++;
}
cout<<vm;
return 0;
}