#include <iostream>
#include <string>
using namespace std;

int main() {
ios::sync_with_stdio(false);
cin.tie(nullptr);

int n;  
string s;  
cin >> n >> s;  

// Conteo total de cada letra en toda la cadena  
int total[26] = {0};  
for (char c : s) {  
    total[c - 'a']++;  
}  

bool en_izquierda[26] = {false};  
int max_letras = 0;  
int cont_izq = 0;  

for (char c : s) {  
    int idx = c - 'a';  

    // Agregar letra a la parte izquierda si no estaba  
    if (!en_izquierda[idx]) {  
        en_izquierda[idx] = true;  
        cont_izq++;  
    }  

    // Quitar una aparición de la parte derecha  
    total[idx]--;  

    // Contar cuántas letras quedan en la derecha  
    int cont_der = 0;  
    for (int i = 0; i < 26; i++) {  
        if (total[i] > 0) cont_der++;  
    }  

    // Actualizar el máximo  
    if (cont_izq + cont_der > max_letras) {  
        max_letras = cont_izq + cont_der;  
    }  
}  

cout << max_letras << endl;  
return 0;

}