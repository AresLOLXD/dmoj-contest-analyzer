#include <iostream>
using namespace std;
int main()
{
    ios_base::sync_with_stdio(0);  cin.tie(0);   cout.tie(0);
	long long int A,B,C;
	cin>>A>>B>>C;
	long long int K=0;
	cin>>K;
	long long int Mayor= 0;
	long long int resultado= 0;

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