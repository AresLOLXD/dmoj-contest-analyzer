#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int N;
    if (!(cin >> N)) return 0;
    vector<int> a(N);
    for (int i = 0; i < N; ++i) {
        if(!(cin >> a[i])) a[i]=0;
        // en el problema 3 significa este
        if (a[i]!= 0) a[i] = 1; 
    }

    // prefijos de oeste (0)
    vector<int> prefWest(N+1, 0);
    for (int i = 0; i < N; ++i) {
        prefWest[i+1] = prefWest[i] + (a[i]==0? 1 : 0);
    }
    int totalEast = 0;
    for (int x : a) if (x==1) totalEast++;

    int prefEast = 0;
    int ans = N;
    for (int i = 0; i < N; ++i) {
        int leftCost = prefWest[i]; // ceros a la izquierda = deben voltear a este

        // estes a la derecha = totalEast - prefEast - (a[i]==1)
        int rightCost = totalEast - prefEast - (a[i]==1? 1 : 0);
        int cur = leftCost + rightCost;
        ans = min(ans, cur);
        if (a[i]==1) prefEast++;
    }
    if (N==1) ans = 0;
    cout << ans << "\n";
    return 0;
}