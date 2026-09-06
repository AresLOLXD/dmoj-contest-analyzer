#include <iostream>
#include <algorithm>
using namespace std;
int main()
{ long long int a;
  long long int b;
  long long int c;
  long long int op;
  long long int m;
  long long int l= 0;
  long long int i= 1;
  long long int y;
  
  cin>>a;
  cin>>b;
  cin>>c;
  
  cin>>l;
 
  m = max (a, b);
  m = max (a, c);
  m = max (b, a);
  m = max (b, c);
  m= max (c, a );
  m= max (c,a);
  
  op = m;
  
     while(i <= l){
          i++;
         op= op * 2;

      }
      
  y = (op + a + b + c)-m; 
  
  cout << y;

    return 0;
}