#include <bits/stdc++.h>
using namespace std;
string cadena;
int conta=0;
int n=0;
int main() {
cin >> n;
cin >> cadena;
for (char c: cadena){
if ( c != ''\0'){
conta++;
}}
cout<< conta/3; 
}