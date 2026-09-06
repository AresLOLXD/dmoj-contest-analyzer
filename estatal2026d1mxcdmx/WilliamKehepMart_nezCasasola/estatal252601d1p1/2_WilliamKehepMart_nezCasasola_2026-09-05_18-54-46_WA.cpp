#include <iostream>
#include <algorithm>
using namespace std;
int main() {
	int i=0,k,o;
    int ar [3];
    while (i<3){
    cin>>ar [i];
    i++;
    }
    cin>>k;
    sort(ar+0,ar+3);
    i=1;
    while (i<=k){
    ar [2]*=2;
    i++;
    }
    cout<<ar [2]+ar [1]+ar [0];
    return 0;
}