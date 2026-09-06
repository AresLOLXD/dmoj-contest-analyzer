#include <bits/stdc++.h>
using namespace std;
int main() {
	int A,B,C,K=0,i=1,AN,SIG,AN1,SIG1,AN2,SIG2,s1,s2,s3;
    cin>>A;
    cin>>B;
    cin>>C;
    cin>>K;
     AN=A*2;
     AN1=B*2;
     AN2=C*2;
     while(K>=i){
           SIG=AN;
           AN=SIG*2;
           SIG1=AN1;
           AN1=SIG1*2;
           SIG2=AN2;
           AN2=SIG2*2;
   i++;
}
s1=AN+B+C;
s2=AN1+A+C;
s3=AN2+B+A;
if(s1>s2&&s1>s3){
    cout<<s1;
}
if(s2>s1&&s2>s3){
    cout<<s2;
}
if(s3>s1&&s3>s2){
    cout<<s3;
}
return 0;
}