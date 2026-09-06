#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'generated/tables'; OUT.mkdir(parents=True,exist_ok=True)
df=pd.read_csv(ROOT/'data/simulation/fem_dataset_528.csv')

damage=pd.cut(df.max_story_drift_ratio,[-np.inf,.005,.01,.02,np.inf],right=False,labels=['none','minor','moderate','severe'])
stiff=pd.cut(df.stiffness_loss_frac,[-np.inf,.60,.80,np.inf],right=False,labels=['low','medium','high'])
resid=pd.Series(np.where(df.post_peak_strength_ratio < .80,'failed','retained'),name='ResidualCapacity')

integrity=pd.DataFrame([
 ['rows',len(df)],['columns',len(df.columns)],['unique CaseID',df.CaseID.nunique()],
 ['fully converged',int((df.ConvergedFully==1).sum())],['partial / last-converged',int((df.ConvergedFully==0).sum())],
 ['mean max ISDR',df.max_story_drift_ratio.mean()],['median max ISDR',df.max_story_drift_ratio.median()],['maximum max ISDR',df.max_story_drift_ratio.max()]
],columns=['item','value'])
integrity.to_csv(OUT/'dataset_integrity_summary.csv',index=False)

rows=[]
for target,s in [('DamageState',damage),('StiffnessLoss',stiff),('ResidualCapacity',resid)]:
    vc=pd.Series(s).value_counts().sort_index()
    for cls,n in vc.items(): rows.append([target,str(cls),int(n),float(n/len(df))])
pd.DataFrame(rows,columns=['Target','Class','Count','Fraction']).to_csv(OUT/'target_class_balance.csv',index=False)

df.groupby(['GeometryFamily','Scale','Regularity'],dropna=False).size().reset_index(name='N').to_csv(OUT/'geometry_population.csv',index=False)
print('Wrote dataset summaries to',OUT)
