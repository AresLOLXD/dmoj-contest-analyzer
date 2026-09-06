#include <iostream>
#include <string>
#include <algorithm>
#include <set>
#include <math.h>
#include <numeric>

using namespace std;

int main (){
    int n{0},max_comunes{0};
    string s;
    cin>>n>>s;
    for (int i=1; i<n;i++){
        set<char> conjuntoReal;
        set<char> conjuntoImaginario;
        for (int j=0;j<i;j++){
        conjuntoReal.insert(s[j]);
    }
    for (int j=i;j<n;j++){
        conjuntoImaginario.insert(s[j]);
    }
  int comunes_act {0};
  for (char letra:conjuntoReal){
      if (conjuntoImaginario.count(letra)>0){
          comunes_act++;
      }
  }
  if (comunes_act>max_comunes){
      max_comunes=comunes_act;
  }
}
cout<<max_comunes<<endl;
return 0;
}