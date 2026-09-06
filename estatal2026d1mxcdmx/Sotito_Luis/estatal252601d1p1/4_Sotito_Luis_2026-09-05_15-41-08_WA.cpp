#include <iostream>
#include <algorithm>
#include <cmath>
using namespace std;

int main(){
    ios_base::sync_with_stdio(0);
    cin.tie(0);

    int a, b , c;
    cin >> a >> b >> c;
    int k;
    cin >> k;
    if(k > 0){
    int may = 0, s = 0;
    if(a > b && a > c){
        may = a;
        s = b + c;
    }else if(b > a && b > c){
        may = b;
        s = a + c;
    }else if(c > a && c > b){
        may = c;
        s = a + b;
    }else{
        may = a;
        s = b + c;
    }
    for(int i = 0; i < k; i++)
        may = may * 2;
    int r = may + s;
    cout << r;
    }

    return 0;
}