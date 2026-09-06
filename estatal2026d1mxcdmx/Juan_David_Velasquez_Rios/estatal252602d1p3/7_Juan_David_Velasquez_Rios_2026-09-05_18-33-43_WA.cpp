#include <iostream>
#include <string>
#include <algorithm>
#include <set>
#include <math.h>
#include <numeric>

using namespace std;

int main (){
    int n{0},max_comunes{0}, comact{0};
    string s;
    int izq[26]={0};
    int der[26]={0};
    cin>>n>>s;
    for (int i=0; i<n;i++){
    der [s[i]-'a']++;
    }
    for (int i=0;i<n-1;i++){
        int idx=s[i]-'a';
        izq[idx]++;
        der[idx]--;
        for (int c=0;c<26;c++){ //C++ Referencia!!!XD
    if (izq[c]>0 && der[c]>>0){
        comact++;
    }
    }
    if (max_comunes<comact){
        max_comunes=comact;
    }
        }
cout<<max_comunes<<endl;
return 0;
}