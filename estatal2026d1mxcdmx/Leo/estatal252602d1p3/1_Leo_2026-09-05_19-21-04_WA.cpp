/******************************************************************************

Welcome to GDB Online.
GDB online is an online compiler and debugger tool for C, C++, Python, Java, PHP, Ruby, Perl,
C#, OCaml, VB, Swift, Pascal, Fortran, Haskell, Objective-C, Assembly, HTML, CSS, JS, SQLite, Prolog.
Code, Compile, Run and Debug online from anywhere in world.

*******************************************************************************/
#include <bits/stdc++.h>

int main()
{   
    int Ncadena;
    std::string cadenita,cadenita_sinB;
    std::multiset<char> total;
    std::cin >> Ncadena >> cadenita;
    
    for(size_t i = 0; i < cadenita.size();i++){
        total.insert(cadenita[i]);
    }
    
    int MaxEncontrados = 0;
    for(int i = 0; i < cadenita_sinB.size();i++){
        int Encontrado = 0;
        for(int z = 0; z < cadenita_sinB.size();z++){
            bool Ps = false,Ps2 = false;
            char P = cadenita_sinB[z];
            bool saltC = false;
            if(z != 0){
                if (cadenita_sinB[z - 1] == cadenita_sinB[z] or cadenita_sinB[z + 1] == cadenita_sinB[z]){
                    saltC = true;
                }
            } 
            if (!saltC){
                for (int x = i; x != 0;x--) {
                    if(P == cadenita_sinB[x]){
                        Ps = true;
                        break;
                    }
                }
                for(int y = i ; y < cadenita_sinB.size();y++){
                    if(P == cadenita_sinB[y]){
                        Ps2 = true;
                        break;
                    }
                }
                
                if(Ps and Ps2) {
                    Encontrado++;
                    Ps = false;
                    Ps2 = false;
                } 
            }
        }
        
        if(i == 0) {
            MaxEncontrados = Encontrado;
        } else {
            if(MaxEncontrados < Encontrado){
                MaxEncontrados = Encontrado;
            }
        }
    }
    std::cout << MaxEncontrados;
    
    return 0;
}