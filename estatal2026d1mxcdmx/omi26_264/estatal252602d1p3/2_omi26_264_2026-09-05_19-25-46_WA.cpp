#include<bits/stdc++.h>
using namespace std;
int main(){
unsigned int n; 
cin>>n;
vector<char>punto(n+1);
vector<char>punto2(n+2);

for (unsigned int i =0; i<n/2; i++){
cin>>punto[i];
}
for (unsigned int i =0; i<(n/2)+1; i++){
cin>>punto2[i];
}


sort(punto.begin(), punto.end());
sort(punto2.begin(), punto2.end());
vector<char>punto3;
for(unsigned int i = 0; i<n; i++){
if (punto[i] != punto[i+1]){
punto3.push_back(punto[i]);  

}
if (punto2[i] != punto2[i+1]){
punto3.push_back(punto2[i]);
}

}
int cont = 0;
sort(punto3.begin(), punto3.end());
for (unsigned int i= 0; i<punto3.size(); i++){
    if (punto3[i] == punto3[i+1]){
       cont++;

    }
}

cout<<cont;
return 0; 
}