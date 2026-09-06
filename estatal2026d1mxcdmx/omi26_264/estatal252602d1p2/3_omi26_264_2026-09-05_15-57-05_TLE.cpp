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
long long int suma  = 0;

for (int  i = 0;  i<n; i++){
    for (int j = 0; j<i; j++){
        if (punto[j] == 0){
        cont++;
        }

    }
     for (int k = i+1; k<n; k++){
        if (punto[k] == 3){
        cont++;
        }

    }
    if (i == 0){
    suma  = cont;
    }
    else if (i != 0 && cont < suma){
        suma = cont;
    }

    cont = 0;

}

cout<<suma;
return 0;
}