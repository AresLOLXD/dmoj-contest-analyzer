#include <bits/stdc++.h>
using namespace std;
int main()
{
	int A,B,C;
	cin>>A>>B>>C;
	int K;
	cin>>K;
	int Mayor;
	int resultado;
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
			resultado= A+B+C;
		}
		if(Mayor==B) {
			B=B*2;
			resultado= A+B+C;
		}
		if(Mayor==C) {
			C=C*2;
			resultado= A+B+C;
		}
	}

	cout<<resultado;
}