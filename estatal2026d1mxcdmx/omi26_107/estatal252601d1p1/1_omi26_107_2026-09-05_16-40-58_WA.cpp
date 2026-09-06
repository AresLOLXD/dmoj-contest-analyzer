#include <bits/stdc++.h>
using namespace std;

#define ll long long int

int main() {
ll f[5]={0};
ll suma =0;
ll mm=0;
ll k=0;
ll i =1;
while (3 >= i){
cin >> f[i];
i++;
}
cin >> k;
i--;
sort(f, f+i+1);
mm = (k *2) * f[3];
suma = mm + f[1]+f[2];
cout << suma;
 return 0;
}