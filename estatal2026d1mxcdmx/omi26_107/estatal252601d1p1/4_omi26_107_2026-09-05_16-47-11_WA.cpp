#include <bits/stdc++.h>
using namespace std;
int main() {
int a, b,c;
int suma =0;
int mm=0;
int k=0;
int i =1;
cin >>a>> b>>c >> k;
int f[5]={a,b,c};
std::sort(f, f+i+1);
mm = (k *2) * f[2];
suma = mm + f[0]+f[1];
cout << suma;
    return 0;
}