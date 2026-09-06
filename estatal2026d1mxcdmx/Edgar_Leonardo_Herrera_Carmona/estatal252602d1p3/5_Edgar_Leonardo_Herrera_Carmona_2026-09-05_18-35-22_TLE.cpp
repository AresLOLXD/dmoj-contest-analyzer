#include <bits/stdc++.h>
using namespace std;

int main(){
    int abcdario[26]={0};
    string n;
    set<char> x, y;
    int num, total=0, rep=0;
    cin>>num>>n;
    for(int a=1; a < num; a++){
        for(int i=0; i < num; i++){
            if( i < a ){
                x.insert(n[i]);
            }else{
                y.insert(n[i]);
            }
        }
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
        total= max(total, rep);  rep=0; x.clear(); y.clear();
        for(int b=0; b < 26; b++){
            abcdario[b]=0;
        }
    }
    cout<<total;
}