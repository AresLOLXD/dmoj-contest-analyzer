#include <bits/stdc++.h>

using namespace std;

int a = 0;
int b = 0;
int c= 0;
int k= 0;


int main() {
    
  cin >> a;
  cin >> b;
  cin >> c;
  cin >> k;
  
  while (k > 0) {
      if (a > b){
          if (a > c){
              a = a * 2;
            
          }else{
              c = c * 2;
          }
      } else{
          if (b > c){
              b = b * 2;
          }else{
              c = c*2;
          }
          
      }
      k = k - 1;
  }
  
  k = a + b;
  k = k + c;
  cout << k;
}