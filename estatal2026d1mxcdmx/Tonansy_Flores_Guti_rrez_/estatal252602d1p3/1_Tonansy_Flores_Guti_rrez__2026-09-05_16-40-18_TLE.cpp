#include <bits/stdc++.h>
using namespace std;

int main() {
    int N;
    cin >> N;

    string S;
    cin >> S;

    int respuesta = 0;

    for (int i = 1; i < N; i++) {
        bool izquierda[26] = {};
        bool derecha[26] = {};

        for (int j = 0; j < i; j++)
            izquierda[S[j] - 'a'] = true;

        for (int j = i; j < N; j++)
            derecha[S[j] - 'a'] = true;

        int total = 0;

        for (int j = 0; j < 26; j++) {
            if (izquierda[j] && derecha[j])
                total++;
        }

        respuesta = max(respuesta, total);
    }

    cout << respuesta << endl;

    return 0;
}