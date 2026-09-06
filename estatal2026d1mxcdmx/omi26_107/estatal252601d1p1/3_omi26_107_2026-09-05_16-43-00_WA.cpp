#include <bits/stdc++.h>
using namespace std;
int main() {
int f[5]={0};
int suma =0;
int mm=0;
int k=0;
int i =1;
while (3 >= i){
cin >> f[i];
i++;
}
cin >> k;
i--;
std::sort(f, f+i+1);
mm = (k *2) * f[3];
suma = mm + f[1]+f[2];
cout << suma;
 return 0;
}