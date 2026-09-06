#include <bits/stdc++.h>
#define ll long long int 
using namespace std;
int main() {
    ll n,a,ccounter=0,tcounter=0,c=0,t=0,cpos=0,tpos=0,r=0,s=0,res=0;
    cin>>n;
    ll rango[n+1]={0};
    for(int i=1;i<=n;i++){
        cin>>a;
        if(a==0){
            ccounter+=1;
            if(ccounter==2){
                cpos=i-1;
                c++;
            }
        }else{
            ccounter=0;
        }
        if(a==3){
            tcounter+=1;
            if(tcounter==2){
                tpos=i-1;
                t++;
            }
        }else{
            tcounter=0;
        }
        rango[i]=a;
    }
    int i=1,j=0;
    if(cpos>0){
        j=cpos+1;
        while(i<cpos){
            if(rango[i]==0){
               r+=1;
            }
            i++;
        }
        while(j<=n){
            if(rango[j]==3){
               r+=1;
            }
            j++;
        }
        i=1;
        j=tpos+1;
        while(i<tpos){
            if(rango[i]==0){
               s+=1;
            }
            i++;
        }
        while(j<=n){
            if(rango[j]==3){
                s+=1;
            }
            j++;
        }
        res=min(r,s);
    }else{
    i=0;
        while(i<=n){
            if(rango[i]==0){
               r+=1;
            }
            i++;
        }
        i=n;
        while(i>=1){
            if(rango[i]==3){
               s+=1;
            }
            i--;
        }
        res=min(r,s);
    }
    cout<<res;
}