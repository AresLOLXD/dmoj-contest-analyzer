#include <stdio.h>
#include <iostream>
using namespace std;
int main()
{

    int n;
    string s;

    cin >> n;
    cin >> s;

    int minimo = 0;

    for (int corte = 1; corte < n; corte++)
    {
        int letras = 0;

        for (char c = 'a'; c <= 'z'; c++)
        {
            bool izquierda = false;
            bool derecha = false;

            for (int i = 0; i < corte; i++)
            {
                if (s[i] == c)
                    izquierda = true;
            }

            for (int i = corte; i < n; i++)
            {
                if (s[i] == c)
                    derecha = true;
            }

            if (izquierda && derecha)
                letras++;
        }

        if (letras > minimo)
            minimo = letras;
    }

    cout << minimo;

return 0;
}