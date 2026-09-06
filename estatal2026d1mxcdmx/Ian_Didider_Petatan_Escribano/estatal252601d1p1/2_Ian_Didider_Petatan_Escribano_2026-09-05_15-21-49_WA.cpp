#include <iostream>
using namespace std;
int main(){
    int a,b,c,k;
    int r=0;
    cin>>a>>b>>c>>k;
    int mayor=0;
    int s=0;
    if(a>b&&a>c){
        mayor=a;
        s=b+c;
    }else if(b>a&&b>c){
        mayor=b;
        s=a+c;
    }else{
        mayor=c;
        s=a+b;
    }
    for(int i=0; i<k; i++){
        mayor=mayor*2;
    }
    r=mayor+s;
    cout<<r;
    return 0;
}