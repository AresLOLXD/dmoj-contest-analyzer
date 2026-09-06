#include <iostream>
using namespace std;

int v[200005];

int main () {
    int n;
    cin >> n;
    int der=0;
    for(int i=0; i<n; i++){
    cin >> v[i];
    if(v[i] == 3) der++;
    }
    int izq =0;
    int ans = 999999;
    for (int i=0; i<n; i++){
        if(v[i] ==3) der--;
        int temp =izq + der--;
        if(temp < ans) ans = temp;
        if(v[i] ==0) izq++;
    }
    cout << ans;
    return 0;
}