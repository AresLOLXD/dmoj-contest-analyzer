#include <bits/stdc++.h>

using namespace std;

int main() {
	int a, b, c, k;
    cin>>a >>b >>c >>k;
    int mayor=0;
    if (a>b && a>c){
        for(int i=0;i<k;i++){
            a*=2;
        }
        mayor=a+b+c;
    } else if( b>a && b>c){
        for(int i=0;i<k;i++){
            b*=2;
        }
        mayor=b+a+c;
    } else if (c>a && c>b){
        for(int i=0;i<k;i++){
            c*=2;
        }
        mayor=c+a+b;
    }
    cout<<mayor;
    return 0;
}