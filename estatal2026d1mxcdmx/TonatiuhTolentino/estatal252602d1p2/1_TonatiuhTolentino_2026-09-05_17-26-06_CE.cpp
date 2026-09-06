long long int n = 0;
int d[200002];
int lider = 0;
int cambios = 0;
int minimo = 999999;
int ca = 0;

int main(){
    cin >> n;

    int i = 0;
    while(i < n){
        cin >> d[i];
        //cout << d[i];
        i++;
    }

    i = 0;
    while(i < n){
        lider = d[i];
        //cout << "lider " << lider << endl;

        

        //Oeste/Izq.
        if(d[i] == 3){
            while(ca < i){
                
                if(d[ca] != d[i]){
                    cambios += 1;
                }
                ca++;
            }
        }
        else{
            if(d[i] == 0){
                ca = n-1;
                while(ca > i){

                    if(d[ca] != d[i]){
                        cambios += 1;
                    }
                    ca--;
                }
            }
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
}