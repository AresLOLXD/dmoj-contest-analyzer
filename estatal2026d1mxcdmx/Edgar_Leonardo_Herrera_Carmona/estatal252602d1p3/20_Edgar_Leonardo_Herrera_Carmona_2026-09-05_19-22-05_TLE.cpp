#include <bits/stdc++.h>
using namespace std;

int main(){
    int abcdario[26]={0};
    string n;
    set<char> x, y;
    int num, total=0, rep=0;
    cin>>num>>n;
    for(int a=0; a < num; a++){
        if(total == 26){
            cout<<total;
            return 0;
        }
            x.insert(n.begin(), n.begin()+a);
            y.insert(n.begin()+a, n.end());
        
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