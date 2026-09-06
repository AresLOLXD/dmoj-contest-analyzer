#include <iostream>
#include <string>
using namespace std;

int main()
{
  int n;
string s;
cin >> n;
cin >> s;
 int izq[26] = {0};
int der[26] = {0};
    for (int i = 0; i < n; i++){
        der[s[i] - 'a']++;
    }
int max= 0;
 for (int corte = 0; corte < n - 1; corte++) {
izq[s[corte] - 'a']++;
der[s[corte] - 'a']--;
int dif = 0;
 for (int i = 0; i < 26; i++){
    if (izq[i] > 0 && der[i] > 0)
{
  dif++;
  }
 }
if (dif > max){
 max = dif;
 }
    }
 cout << max;
return 0;
}