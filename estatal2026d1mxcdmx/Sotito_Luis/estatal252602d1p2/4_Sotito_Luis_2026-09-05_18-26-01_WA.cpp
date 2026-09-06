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
    int v = 0, aux = 0, m = 0;
    for(int i = 0; i < n; i++){
        if(arr[i - 1] != 0){
            v++;
            aux = v;
        }else if(arr[i + 1] != 3){
            v++;
            aux = v;
        }
        if(aux == v)
            m = v;
        v = 0;
    }
    cout << m;

    return 0;
}