#include <iostream>
using namespace std;
int main() {
long long int n, i=0,i2=0,mc,l;
cin>>n;
long long int ar [n];
while (i<n){
    cin>>ar [i];
    i++;
}
i=0;
long long int car [n];
while(i<n){
    car [i]=0;
    i++;
}
i=0;
while (i<n){
l=ar [i];
while (i2<i){
    if (ar [i2]!=3){
        car [i]++;
    }
    i2++;
}
            if(i==0){
                i2++;
            }else if (i != 0){
            i2+=2;
            }
        
    while (i2<n){
        if (ar [i2]!=0){
            car [i]++;
        }
            i2++;
    }
         if (i==0){
            mc=car [0];
         }else if (i != 0){
        if(car [i-1]>car [i]&&car [i]<mc){
         mc=car [i];
        }
         }
    i2=0;
    i++;
}
cout <<mc;


return 0;
}