#include <bits/stdc++.h>

using namespace std;

int main() {
    int n;
    cin>>n;
    int arr[n];
    for(int i=0;i<n;i++){
        cin>>arr[i];
    }
    int cambios=0,total=0;
    for(int i=0;i<n;i++){
        if(arr[i]==0){
            for(int j=i;j<n;j++){
                    if(arr[i] != arr[j]){
                        cambios++;
                    }
                }
            for(int j=i-1;j>=0;j--){
                if(arr[i] == arr[j]){
                        cambios++;
                    }
            }
        } else if (arr[i] == 3){
            for(int j=i;j>=0;j--){
                    if(arr[i] != arr[j]){
                        cambios++;
                    }
                }           
            for(int j=i+1;j<n;j++){
                    if(arr[i] == arr[j]){
                        cambios++;
                    }
                }

        }
        if (i==0){
            total=cambios;
        }
        if (cambios<total){
            total=cambios;
        }
        cambios=0;
    }
    cout<<total;
    return 0;
}