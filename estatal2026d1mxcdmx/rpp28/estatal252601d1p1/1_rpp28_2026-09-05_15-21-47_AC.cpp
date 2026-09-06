#include <bits/stdc++.h>
#define ll long long int 
using namespace std;
ll k, res;
ll suma[5];

int main() {
    for(int i=1; i<=3; i++){
        cin>>suma[i];
    }
        cin >> k;
    for(int i=1; i<=k; i++){
        sort(suma+1, suma+1+3);
        suma[3]*=2;
    }
    res=suma[1]+suma[2]+suma[3];
    cout << res;

}