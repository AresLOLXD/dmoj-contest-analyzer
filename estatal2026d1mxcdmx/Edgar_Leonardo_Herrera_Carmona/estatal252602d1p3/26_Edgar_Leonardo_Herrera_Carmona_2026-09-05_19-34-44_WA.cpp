#include <bits/stdc++.h>
using namespace std;

int main(){
    int abcdario[26]={0};
    string n;
    int tiempo=0;
    int num, total=0, rep=0;
    cin>>num>>n;
    for(int a=1; a < num; a++){
        if(total == 26){
            cout<<total;
            return 0;
        }
        set<char> x, y;
            x.insert(n.begin(), n.begin()+a);
            y.insert(n.begin()+a, n.end());
        
        for(int i : x){
            abcdario[i-97]++;
        }
        for(int i : y){
            abcdario[i-97]++;
        }
        for(int i=0; i < 26; i++){
            if( abcdario[i] == 2 ){
                rep++;
            }
            abcdario[i]=0;
        }
        if (total == max(total, rep)){
            tiempo++;
        }else{
            total=rep; tiempo=0;
        }
        if(tiempo > 15){
            cout<<total; return 0;
        }  rep=0;  
    }
    cout<<total;
}