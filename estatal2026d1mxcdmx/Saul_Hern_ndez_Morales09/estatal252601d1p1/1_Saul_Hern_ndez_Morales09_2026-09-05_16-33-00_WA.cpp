#include <iostream>

using namespace std;

int main() {
    double num1, num2,num3, suma, multiplicacion;

    cout << "Ingresa el primer número: ";
    cin >> num1;

    cout << "Ingresa el segundo número: ";
    cin >> num2;
    
    cout << "Ingresa el tercer numero: ";
    cin >> num3;

    // Calcular suma y multiplicación
    multiplicacion = num1 * 2;
    suma = multiplicacion + num2 + num3;

    // Mostrar resultados

    cout << "la suma es: " << suma << endl;

    return 0;
}