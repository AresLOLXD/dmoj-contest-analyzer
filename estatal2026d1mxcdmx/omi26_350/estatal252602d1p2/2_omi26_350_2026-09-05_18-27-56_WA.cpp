#include <iostream>
#include <algorithm> // Para usar la función std::max

using namespace std;

int main() {
    // Optimizamos la velocidad de entrada/salida de C++
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    // Usamos 'long long' para evitar desbordamiento (overflow) de memoria
    long long a, b, c;
    int k;

    // Leemos los 3 números enteros y las K operaciones
    if (cin >> a >> b >> c >> k) {
        
        // Encontramos el número más grande de los tres
        long long maximo = max({a, b, c});
        
        // Calculamos la suma base de los tres números
        long long suma_total = a + b + c;
        
        // El número máximo se duplica K veces, lo que equivale a multiplicarlo por 2^K.
        // El operador (maximo << k) calcula eficientemente: maximo * potencia(2, k)
        long long maxima_suma_posible = (suma_total - maximo) + (maximo << k);
        
        // Mostramos el resultado final
        cout << maxima_suma_posible << "\n";
    }

    return 0;
}