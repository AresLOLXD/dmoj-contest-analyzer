#include <bits/stdc++.h>
using namespace std;

long long int n = 0;
int d[200002];
int cambios = 0;
int minimo = 999999;
int long long ca = 0;

int oeste = 0;
int este = 3;

int main(){
    cin >> n;

    for(int i = 0; i < n; i++){
        cin >> d[i];
    }
    /*
    int i = 0;
    while(i < n){
        cin >> d[i];
        //cout << d[i];
        i++;
    }
    */
    int i = 0;
    while(i < n){
        
        for(int ca = 0; ca < i; ++ca){
            if(d[ca] != este){
                cambios += 1;
            }
        }
        for(int ca = n - 1; i < ca; --ca){
            if(d[ca] != oeste){
                cambios += 1;
            }
        }
        /*
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
        */
        //cout << "cambios " << cambios << endl;
        
        if(cambios < minimo){
            minimo = cambios;
            //cout << "minimo " << minimo << endl;
        }

        cambios = 0;
        i++;
    }
        cout << minimo;
        
        return 0;
}