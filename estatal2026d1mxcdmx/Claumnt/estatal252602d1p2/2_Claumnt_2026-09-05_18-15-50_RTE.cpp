#include <bits/stdc++.h>

using namespace std;

int dato [100] = {};
long long int n = 0;
long long int i = 0;
long long int con = 0;
long long int posic= 0;
long long int mn = 0;
long long int resu = 0;

int main(){
  cin >> n;
  while (i < n){
    
          cin >> dato [i];
          
      i++;
  }
  i = 0;
  
 while (con < n){
  posic = i;
  while ( i < n) {
      if (dato [i] == 3){
          mn = mn + 1;
          i++;
          
      }
        i++; 
 
  }
  con++;
  if ( resu == 0){
       resu == mn;
   }
   
   if (resu > mn){
      resu = mn;
   }
  
  
  }
  cout << mn;
  
 

}