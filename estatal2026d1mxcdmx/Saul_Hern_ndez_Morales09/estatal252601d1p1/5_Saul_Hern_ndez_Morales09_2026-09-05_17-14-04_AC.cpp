#include <bits/stdc++.h>
using namespace std;

int main() {
    long long A, B, C;
    int K;

    cin >> A >> B >> C >> K;

    for (int i = 0; i < K; i++) {
        if (A >= B && A >= C)
            A *= 2;
        else if (B >= A && B >= C)
            B *= 2;
        else
            C *= 2;
    }

    cout << A + B + C << '\n';

    return 0;
}