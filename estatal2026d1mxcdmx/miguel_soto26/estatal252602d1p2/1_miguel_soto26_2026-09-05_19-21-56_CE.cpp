#include <iostream>
#include <vector>
#include <algorithm>

using namespace std; 

int moin (){ 
    //Optimizacion de entrada/salida rapida 
    ios_base::sync_with_stdio(false);
    cinotie (NULL);
    
    int Ni
    if (!( cin>>N)) return 0 ;
    
    vector cinte v(N);
    int personas_a_la_derecha_mirando_este= 0;
    
    for ( int i=0; i<Ni i++) {
        cin >> v[i];
        //contamos cuantas personas inicialmente miran al este (3)
        if (v[i]i==3) {
            personas_a_la_izquierda_mirando_este++,
        }
}

int personas_a_la_izquierda_mirando_oeste=0;
int min_cambos=N+1;

//probamos cada posicion como lider 
for (int i=0;i <N; i++) {
    if (u[i]==3){ 
        personas_a_la_derecha_mirando_este--i
    }
    
    //para las personas a la izquierda , deben mirar al este
    //cambian las que actualmente miran al oeste (0).
    int cambios_izquierda_personas_a_la_izquierda_mirando_oeste;
    
    //para las personas a la derecha , deben mirara al este; 
    //cambia los que actualmente miran al este (3) 
    int camnios a derecha = personas_a_la_derecha_mirando_este ;
    
    int cambios_totales= cambios_izquierda+cambios_derecha ;
    min cambios = min (min_cambios,cambios  totales ) ;

   if ( v [i]==0 {
       
       personas_a_la_izquierda_mirando_oeste++ ; 
       
       }
      }
      count<<min_cambio<<"\n";
      
      return 0;
      
}