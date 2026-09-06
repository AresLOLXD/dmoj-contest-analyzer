#include <bits/stdc++.h>
using namespace std;

int main(){
    int hola=0;
    string n;
    set<char> x, y;
    int num, total=0, rep=0;
    cin>>num>>n;
    for(int a=( num%26 )+1; a < (num-num%26); a++){
        for(int i=0; i < num; i++){
            
            if( i < a ){
                x.insert(n[i]);
            }else{
                y.insert(n[i]);
            }
        }
        do{
            int abcdario[26]={0};
            for(int i : x){
                abcdario[i-97]++;
            }
            for(int j : y){
                abcdario[j-97]++;
            }
            for(int i : abcdario){
                if( i == 2 ){
                    rep++;
                }
            }
        }while(hola!=0);
        total= max(total, rep);  rep=0; x.clear(); y.clear();
        
    }
    cout<<total;
}