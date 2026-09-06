#include <iostream>
using namespace std;
int main(){
    int n,x,y,r=1;;
    cin>>n;
    char arre[n];
    for(int i=0; i<n; i++){
        cin>>arre[i];
    }
    x=0;
    y=n-1;
    for(int i=0; i<n/2; i++){
        if(arre[x]!=arre[y]){
            r++;
        }
        x++;
        y--;
    }
    cout<<r;
    return 0;
}