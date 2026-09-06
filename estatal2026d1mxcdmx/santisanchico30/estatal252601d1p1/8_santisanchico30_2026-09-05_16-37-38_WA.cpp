#include <bits/stdc++.h>
using namespace std;
int main()
{
    ios_base::sync_with_stdio(0);  cin.tie(0);   cout.tie(0);
	long long int A,B,C;
	cin>>A>>B>>C;
	int A2,B2,C2;
	A2=A;
	B2=B;
	C2=C;
	long long int K=0;
	cin>>K;
	int resultado=0;
	int resultadob=0;
	int resultadoc=0;
	for(int i=1; i<=K; i++){
	    A=A*2;
	    resultado= A+B+C;
	}
		for(int i=1; i<=K; i++){
	    B=B*2;
	    resultadob= A2+B+C;
	}
		for(int i=1; i<=K; i++){
	    C=C*2;
	    resultadoc= A2+B2+C;
	}
	if(resultado>resultadob and resultado>resultadoc){
	    cout<<resultado;
	}
		if(resultadob>resultado and resultadob>resultadoc){
	    cout<<resultadob;
	}
		if(resultadoc>resultadob and resultadoc>resultado){
	    cout<<resultadoc;
	}
	
}