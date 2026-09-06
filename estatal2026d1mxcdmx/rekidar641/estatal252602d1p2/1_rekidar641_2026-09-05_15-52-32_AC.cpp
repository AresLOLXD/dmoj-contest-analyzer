#include <bits/stdc++.h>
using namespace std;
#define ll long long
int main() {
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(NULL);
    int n; cin >> n;
    vector<int> a(n);
    for(int i = 0; i < n; i++){
        cin >> a[i];
    }
    int der=0;
    for(int x : a){
        if(x==0) der++;
    }
    int izq=0;
    int r=n;
    for(int i = 0; i < n; i++){
        if(a[i] == 0)
            der--;
        int derc = (n-i-1) - der;
        int cam = izq+derc;
        r = min(r,cam);
        if(a[i] != 3)
            izq++;
    }
    cout << r;
}