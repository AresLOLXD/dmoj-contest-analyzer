#include <iostream>
#include <algorithm>
#include <vector>
using namespace std;

int main()
{
ios_base::sync_with_stdio(false);
cin.tie(NULL);
int n;
if (!(cin >> n)) return 0;

vector <int> a(n);
int derecha_este=0;
for (int i = 0; i < n; ++i) {cin>>a[i];
    //contamos primero cuantos miran al este (3) en toda la hilera
    if (a[i]==3){
        derecha_este++;
        
    }
}
int izquierda_oeste=0;
int min_cambios =n; 
// inicializa con un valor grande
for (int i =0; i <n; ++i);
}