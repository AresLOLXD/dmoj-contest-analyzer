#include <bits/stdc++.h>
using namespace std;
string cadena;
int conta=0;
int n=0;
int main() {
cin >> n;
cin >> cadena;
for (char c: cadena){
conta++;
}

cout<< conta/3; 
}