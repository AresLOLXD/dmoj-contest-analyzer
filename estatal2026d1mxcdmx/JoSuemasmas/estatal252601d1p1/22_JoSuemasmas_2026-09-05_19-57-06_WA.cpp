#include <iostream>
#include <algorithm>
using namespace std;
int main()
{ long long int a=0;
  long long int b=0;
  long long int c=0;
  long long int op=0;
  long long int m=0;
  long long int l= 0;
  long long int i= 1;
  long long int y=0;
  
  cin>>a;
  cin>>b;
  cin>>c;
  
  cin>>l;
 m = max (a, c);
  m = max (c, b);

  op = m;
  
     while(i <= l){
          i++;
         op= op * 2;

      }
      
  y = (op + a + b + c)-m; 
  
  cout << y;

    return 0;
}