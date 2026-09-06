#include <bits/stdc++.h>
using namespace std;

int main(){
    int abcdario[26]={0};
    string n;
    int num;
    cin>>num>>n;
    num=0;
    for(char i : n){
        abcdario[i-97]++;
    }
    for(int j : abcdario){
        if( j >= 2 ){
            num++;
        }
    }
    cout<<num;
}