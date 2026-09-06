#include <iostream>
using namespace std;
int main(){
    int n,lid,r=0;
    cin>>n;
    int num[n];
    for(int i=0; i<n; i++){
        cin>>num[i];
    }
    int menor=n;
    lid=1;
    for(int i=0;i<n;i++){
        for(int j=0; j<lid; j++){
            if(num[j]==0){
                r++;
            }
        }
        for(int l=n-1; l>lid; l--){
            if(num[l]==3){
                r++;
            }
        }
        lid++;
        if(r<menor){
            menor=r;
        }
        r=0;
    }
    cout<<menor;
    return 0;
}