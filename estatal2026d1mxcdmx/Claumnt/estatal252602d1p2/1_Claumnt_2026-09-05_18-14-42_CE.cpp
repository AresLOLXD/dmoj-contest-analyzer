#include <bits/stdc++.h>

using namespace std;

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