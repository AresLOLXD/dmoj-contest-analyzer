#include <iostream>
#include <array>
#include <format>

int main() {
    // Usamos std::array para almacenar los 4 números de forma limpia
    std::array<double, 4> nums{};

    // Bucle para solicitar los números de manera eficiente
    for (size_t i = 0; i < nums.size(); ++i) {
        std::cout << std::format("Ingresa el número {}: ", i + 1);
        std::cin >> nums[i];
    }

    // Calcular multiplicación y suma
    double multiplicacion = nums[0] * nums[1];
    double suma = multiplicacion + nums[2] + nums[3];

    // Mostrar resultados usando std::format (C++20)
    std::cout << std::format("La suma es: {}\n", suma);

    return 0;
}