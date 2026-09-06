#include <iostream>
#include <string>
#include <algorithm>
#include <set>
#include <math.h>
#include <numeric>

using namespace std;

int main (){
    long long int linea [200000]={},num_personas {0}, i{0},volteos_a{0},volteos_b{0};
    cin>>num_personas;
    while (i!=num_personas){
        cin>>linea[i];
        i++;
    }
    i=0;
    long long int j=num_personas-1;
    while(i!=num_personas){
        if (linea[i]==0){
            volteos_a=volteos_a+1;
        }
        if (linea[j]==3){
            volteos_b=volteos_b+1;
        }
        i++;
        j--;
    }
    cout<<max (volteos_b, volteos_a)
}