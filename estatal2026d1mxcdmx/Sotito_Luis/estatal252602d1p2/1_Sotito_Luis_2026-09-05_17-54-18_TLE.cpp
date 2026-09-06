#include <iostream>
#include <algorithm>
#include <cmath>
using namespace std;

int main(){
    ios_base::sync_with_stdio(0);
    cin.tie(0);

    int n;
    cin >> n;
    int arr[n];
    for(int i = 1; i <= n; i++)
        cin >> arr[i];
    int l = 0, v = 0, r = 0;
    int menor = 99999999;
    for(int i = 0; i < n; i++){
        l = arr[i];
        for(int j = 0; j < n - 1; j++){
            if(arr[j + 1] != l){
                v++;
            }
        }
        r = v;
        if(r < menor)
            menor = v;
        v = 0; 
    }
    
    cout << menor;

    return 0;
}