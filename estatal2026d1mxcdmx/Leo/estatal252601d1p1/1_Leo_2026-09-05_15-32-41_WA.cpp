/******************************************************************************

Welcome to GDB Online.
GDB online is an online compiler and debugger tool for C, C++, Python, Java, PHP, Ruby, Perl,
C#, OCaml, VB, Swift, Pascal, Fortran, Haskell, Objective-C, Assembly, HTML, CSS, JS, SQLite, Prolog.
Code, Compile, Run and Debug online from anywhere in world.

*******************************************************************************/
#include <bits/stdc++.h>

std::array<int,3> calculo(std::array<int,3> numeross,int K){
    std::array<int,3> combinaciones;
    
    for (size_t i = 0; i < 3; i++){
        int TransformNum = numeross[i],NumeroB = numeross[i],Suma = 0;
        
        for(int z = 0; z < K;z++){
            TransformNum = TransformNum * 2;
        }
        
        for(int X = 0; X < 3;X++){
            if(numeross[X] != NumeroB){
                Suma += numeross[X];
            }
            if(X == 0) {
                Suma += TransformNum;
            }
        }
        combinaciones[i] = Suma;
    }
    return combinaciones;
}


int main()
{
    std::array<int,3> numeros,combinaciones1;
    int k;
    for (int i = 0; i < 3 ;i++) {
        std::cin >> numeros[i];
    }
    
    std::cin >> k;
    
    combinaciones1 = calculo(numeros,k);
    int Mvalor = 0;
    for (int i = 0; i < 3;i++) {
        if(combinaciones1[i] > Mvalor) {
            Mvalor = combinaciones1[i];
        }
    }
    
    std::cout << Mvalor;
    return 0;
}