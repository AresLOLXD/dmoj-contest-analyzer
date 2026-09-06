// Source: https://usaco.guide/general/io

#include <algorithm>
#include <bits/stdc++.h>
#include <functional>
#include <iostream>
#include <vector>
using namespace std;

int main() {
	int a, b, c, k;
    long long mayor = 0;
    long long suma = 0; 
    vector<int> nums;

    cin >> a >> b >> c;
	cin >> k;

    nums.push_back({a});
    nums.push_back({b});
    nums.push_back({c});

    sort(nums.begin(), nums.end(), greater<int>());
    mayor = nums[0];

    for (int i = 0; i < k; i++) {
        mayor = mayor * 2;
    }
    suma += mayor;
    suma += nums[1];
    suma += nums[2];
    cout << suma;
}