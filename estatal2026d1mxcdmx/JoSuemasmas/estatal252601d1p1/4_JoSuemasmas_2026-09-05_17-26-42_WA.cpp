#include <iostream>
#include <algorithm>
using namespace std;
int main()
{ int a;
  int b;
  int c;
  int op;
  int m;
  int l= 1;
  int i= 1;
  int y;
  
  cin>>a;
  cin>>b;
  cin>>c;
  
  cin>>l;
 
  m = max (a, c);
  m = max (a, b);
  
  op = m;
  
     while(i <= l){
          i++;
         op= op * 2;

      }
      
  y = (op + a + b + c); 
  
  cout << y;

    return 0;
}