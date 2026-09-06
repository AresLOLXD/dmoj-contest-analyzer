#include <bits/stdc++.h>

using namespace std;

int main() {
int n;
cin>>n;
vector<int>punto(n);
for (int i = 0; i<n; i++){
cin>>punto[i];
}

int cont = 0;
int cont2 = 0;
int cont3 = 0;
int suma  = 0;

for (int  i = n;  i!=0; i--){
if(punto[i] == 3){
    cont2++;
}

for (int j = i-1; j > 0; j--){
if (punto[j] == 0){
    cont++;
}
}     
cont3 = cont+cont2;
if(i == n){
    suma = cont3;    
}

if (suma>cont3){
suma  = cont3;
}

cont = 0;



}
cout<<suma;
return 0;
}