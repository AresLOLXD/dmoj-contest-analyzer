/******************************************************************************

Welcome to GDB Online.
GDB online is an online compiler and debugger tool for C, C++, Python, Java, PHP, Ruby, Perl,
C#, OCaml, VB, Swift, Pascal, Fortran, Haskell, Objective-C, Assembly, HTML, CSS, JS, SQLite, Prolog.
Code, Compile, Run and Debug online from anywhere in world.

*******************************************************************************/
#include <bits/stdc++.h>

int main()
{
    int N,X,este = 0 ,oeste = 0;
    std::vector<int> personitas;
    std::cin >> N;
    
    for(int i = 0;i < N;i++) {
        std::cin >> X;
        personitas.push_back(X);
    }
    
    
    int Minimo = 0;
    for(size_t i = 0; i < personitas.size();i++){
        int Cambios = 0;
        int lider = i; 
        
        for(size_t x = i;x != 0;x--) {
            if(personitas[x] != 3){
                Cambios++;
            }
        }
        
        for(size_t x = i;x < personitas.size();x++){
            if(personitas[x] != 0){
                Cambios++;
            }
        }
        
        if(i == 0){
            Minimo = Cambios;
        } else {
            if(Cambios < Minimo and Cambios != 0){
                Minimo = Cambios;
            }
        }
    }
    
    std::cout << Minimo  << std::endl;
    return 0;
}