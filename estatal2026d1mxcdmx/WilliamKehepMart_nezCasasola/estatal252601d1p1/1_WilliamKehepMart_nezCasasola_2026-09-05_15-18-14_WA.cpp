#include <iostream>
#include <algorithm>
using namespace std;
int main() {
	int i=0,k,o;
    int ar [3];
    while (i<3){
    cin>> ar [i];
    i++;
    }
    cin>>k;
    sort(ar+0,ar+3);
    i=0;
    while (i<k){
    ar [2]*=2;
    i++;
    }
    o=ar [2] + ar [1] + ar [0];
    cout<<o;
    return 0;
}