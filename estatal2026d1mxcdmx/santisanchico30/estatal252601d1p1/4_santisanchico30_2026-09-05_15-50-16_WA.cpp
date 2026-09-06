#include <bits/stdc++.h>
using namespace std;
int main()
{
	long long int A,B,C;
	cin>>A>>B>>C;
	long long int K;
	cin>>K;
	long long int Mayor;
	long long int resultado;
	long long int x;
	if(A>B and A>C) {
		Mayor=A;
	}
	if(B>A and B>C) {
		Mayor=B;
	}
	if(C>A and C>B) {
		Mayor=C;
	}
	for(int i=1; i<=K; i++) {
		if(Mayor==A) {
			A=A*2;
			Mayor=A;
			resultado= A+B+C;
		}
		if(Mayor==B) {
			B=B*2;
			Mayor=B;
			resultado= A+B+C;
		}
		if(Mayor==C) {
			C=C*2;
			Mayor=C;
			resultado= A+B+C;
		}
	}

	cout<<resultado;
}