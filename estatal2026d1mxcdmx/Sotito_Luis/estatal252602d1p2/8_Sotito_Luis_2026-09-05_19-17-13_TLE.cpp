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
    int v = 0;
    for(int i = 0; i < n; i++){
        for(int j = 1; j < n - 1; j++){
            if(j > i){
                if(arr[j] != 0)
                    v++;
            }else if(i > j){
                if(arr[j] != 3)
                    v++;
            }
        }
    }
    cout << v;

    return 0;
}