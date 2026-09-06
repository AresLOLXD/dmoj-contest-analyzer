#include <bits/stdc++.h>
using namespace std;

long long int n = 0;
long long int d[20000002];
int lider = 0;
int cambios = 0;
int minimo = 999999;
long long int ca = 0;

int oeste = 0;
int este = 3;

int main(){
    cin >> n;

    long long int i = 0;
    while(i < n){
        cin >> d[i];
        //cout << d[i];
        i++;
    }

    i = 0;
    while(i < n){
        lider = d[i];
        //cout << "lider " << lider << endl;

        ca = 0;
        while(ca < i){
            if(d[ca] != este){
                cambios += 1;
            }
            ca++;
        }
        ca = n - 1;
        while(i < ca){
            if(d[ca] != oeste){
                cambios += 1;
            }
            ca--;
        }

        //cout << "cambios " << cambios << endl;
        
        if(cambios < minimo && cambios != 0){
            minimo = cambios;
            //cout << "minimo " << minimo << endl;
        }

        cambios = 0;
        i++;
    }
        cout << minimo;
        
        return 0;
}