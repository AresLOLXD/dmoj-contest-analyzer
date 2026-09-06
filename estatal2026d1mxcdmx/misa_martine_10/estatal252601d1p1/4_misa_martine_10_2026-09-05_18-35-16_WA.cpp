#include <iostream>
using namespace std;

int main() {

    int a , b , c;
    cin >> a >> b >> c;
    int k;
    cin >> k;
    int s1 , s2 , s3 , m = 0;

    m = a * 2;
    s1 = m + b + c;
    m = b * 2;
    s2 = a + m + c;
    m = c * 2;
    s3 = a + b + m;

    if(s1 > s2 && s1 > s3){
        cout << s1;
    }else if(s2 > s1 && s2 > s3){
        cout << s2;
    }else if(s3 > s1 && s3 > s2){
        cout << s3;
    }

    return 0;
    }