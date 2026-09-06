#include <iostream>
using namespace std;
int main(){
    int n,x,y,m;
    cin>>n;
    char arre[n];
    for(int i=0; i<n; i++){
        cin>>arre[i];
    }
    x=0;
    y=n-1;
    if(n%2==1){
        n=n-1;
    }
    m=n/2;
    int r=1;
    for(int i=0; i<m; i++){
        if(arre[x]!=arre[y]){
            r++;
        }
        x++;
        y--;
    }
    cout<<r;
    return 0;
}