#!/usr/bin/env python3
"""Reference implementation of the final leakage-controlled inference protocol.

The canonical manuscript numbers are archived under results/. This module provides a
transparent protocol-level implementation of target construction, foldwise evidence
categorization, the expert-specified Bayesian topology, target-specific same-scalar
withholding, benchmark classifier definitions, and validation splits.

Install requirements-model.txt before using the Bayesian-network functions.
"""
from __future__ import annotations
from pathlib import Path
import argparse
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
TARGETS=['DamageState','StiffnessLoss','ResidualCapacity']
DESIGN=['ConcreteStrength','SteelYield','ColumnSectionClass','BeamSectionClass','GravityLoadLevel','StructuralConfigurationClass']
MECHANISM=['EarlyDeformationClass','MemberResponseRegime']
RESPONSE=['MaximumInterstoryDriftClass','BaseShearClass','ColumnSectionCurvatureClass','BeamSectionCurvatureClass','StiffnessDegradationClass','PostPeakStrengthRetentionClass']
ALL_EVIDENCE=DESIGN+MECHANISM+RESPONSE
SAME_SCALAR={'DamageState':'MaximumInterstoryDriftClass','StiffnessLoss':'StiffnessDegradationClass','ResidualCapacity':'PostPeakStrengthRetentionClass'}

STATES={
 'ConcreteStrength':['low','medium','high'],'SteelYield':['low','medium','high'],
 'ColumnSectionClass':['low','medium','high'],'BeamSectionClass':['low','medium','high'],
 'GravityLoadLevel':['low','medium','high'],
 'StructuralConfigurationClass':['regular_2story_2bay','regular_3story_2bay','regular_3plus_story_3bay','stilted_2story_2bay','stilted_3story_2bay'],
 'EarlyDeformationClass':['low','medium','high'],'MemberResponseRegime':['beam','balanced','column'],
 'MaximumInterstoryDriftClass':['none','minor','moderate','severe'],
 'BaseShearClass':['low','medium','high'],'ColumnSectionCurvatureClass':['low','medium','high'],'BeamSectionCurvatureClass':['low','medium','high'],
 'StiffnessDegradationClass':['low','medium','high'],'PostPeakStrengthRetentionClass':['failed','retained'],
 'DamageState':['none','minor','moderate','severe'],'StiffnessLoss':['low','medium','high'],'ResidualCapacity':['failed','retained']
}

def three(v,lo,hi,labels=('low','medium','high')):
    if pd.isna(v): return np.nan
    return labels[0] if v < lo else (labels[1] if v < hi else labels[2])

def configuration_class(row):
    if row['Regularity']=='stilted':
        return 'stilted_2story_2bay' if int(row['n_stories'])==2 else 'stilted_3story_2bay'
    if int(row['n_stories'])==2 and int(row['n_bays'])==2: return 'regular_2story_2bay'
    if int(row['n_stories'])==3 and int(row['n_bays'])==2: return 'regular_3story_2bay'
    return 'regular_3plus_story_3bay'

def add_fixed_targets_and_design(df):
    d=df.copy()
    d['DamageState']=d.max_story_drift_ratio.map(lambda x:'none' if x<.005 else 'minor' if x<.01 else 'moderate' if x<.02 else 'severe')
    d['StiffnessLoss']=d.stiffness_loss_frac.map(lambda x:'low' if x<.60 else 'medium' if x<.80 else 'high')
    d['ResidualCapacity']=d.post_peak_strength_ratio.map(lambda x:'failed' if x<.80 else 'retained')
    d['ConcreteStrength']=d.fc_MPa.map(lambda x:three(x,30,36))
    d['SteelYield']=d.fy_MPa.map(lambda x:three(x,430,470))
    d['ColumnSectionClass']=(d.b_col_mm*d.h_col_mm).map(lambda x:three(x,160000,210000))
    d['BeamSectionClass']=(d.b_beam_mm*d.h_beam_mm).map(lambda x:three(x,140000,190000))
    d['GravityLoadLevel']=d.gravity_per_node_kN.map(lambda x:three(x,200,260))
    d['StructuralConfigurationClass']=d.apply(configuration_class,axis=1)
    d['EarlyDeformation']=d.roof_disp_at_80Vmax_mm/(d.H_mm*d.n_stories)
    d['MaximumInterstoryDriftClass']=d['DamageState']
    d['StiffnessDegradationClass']=d['StiffnessLoss']
    d['PostPeakStrengthRetentionClass']=d['ResidualCapacity']
    return d

def learn_tertiles(train):
    return {
      'EarlyDeformation':tuple(train.EarlyDeformation.quantile([1/3,2/3])),
      'MemberResponseRegime':tuple(train.column_to_beam_curvature_ratio.quantile([1/3,2/3])),
      'BaseShearClass':tuple(train.max_base_shear_kN.quantile([1/3,2/3])),
      'ColumnSectionCurvatureClass':tuple(train.max_column_curvature.quantile([1/3,2/3])),
      'BeamSectionCurvatureClass':tuple(train.max_beam_curvature.quantile([1/3,2/3])),
    }

def apply_foldwise_evidence(df,thr):
    d=df.copy()
    d['EarlyDeformationClass']=d.EarlyDeformation.map(lambda x:three(x,*thr['EarlyDeformation']))
    d['MemberResponseRegime']=d.column_to_beam_curvature_ratio.map(lambda x:three(x,*thr['MemberResponseRegime'],labels=('beam','balanced','column')))
    d['BaseShearClass']=d.max_base_shear_kN.map(lambda x:three(x,*thr['BaseShearClass']))
    d['ColumnSectionCurvatureClass']=d.max_column_curvature.map(lambda x:three(x,*thr['ColumnSectionCurvatureClass']))
    d['BeamSectionCurvatureClass']=d.max_beam_curvature.map(lambda x:three(x,*thr['BeamSectionCurvatureClass']))
    return d

def build_edges(topology='baseline'):
    edges=[]
    for c in DESIGN: edges += [(c,'DamageState'),(c,'StiffnessLoss')]
    edges += [('EarlyDeformationClass','DamageState'),('MemberResponseRegime','DamageState'),('MemberResponseRegime','StiffnessLoss'),('DamageState','StiffnessLoss')]
    for r in RESPONSE: edges += [('DamageState',r),('StiffnessLoss',r)]
    edges += [('MemberResponseRegime','ResidualCapacity'),('DamageState','ResidualCapacity'),('StiffnessLoss','ResidualCapacity')]
    edges += [(r,'ResidualCapacity') for r in RESPONSE]
    if topology=='early_deformation_to_stiffness': edges.append(('EarlyDeformationClass','StiffnessLoss'))
    elif topology=='no_damage_to_stiffness': edges=[e for e in edges if e!=('DamageState','StiffnessLoss')]
    elif topology=='mediated_residual': edges=[e for e in edges if not (e[1]=='ResidualCapacity' and e[0] in RESPONSE)]
    elif topology!='baseline': raise ValueError(topology)
    return edges

def evidence_for(target,regime='controlled'):
    if regime=='full': return list(ALL_EVIDENCE)
    if regime=='controlled': return [c for c in ALL_EVIDENCE if c!=SAME_SCALAR[target]]
    if regime=='design_only': return list(DESIGN)
    raise ValueError(regime)

def get_splits(df,target):
    from sklearn.model_selection import RepeatedStratifiedKFold
    splitter=RepeatedStratifiedKFold(n_splits=5,n_repeats=3,random_state=42)
    return splitter.split(df,df[target])

def benchmark_models():
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
    from sklearn.dummy import DummyClassifier
    return {
      'Logistic regression':LogisticRegression(C=.5,class_weight='balanced',max_iter=4000),
      'Random forest':RandomForestClassifier(n_estimators=300,class_weight='balanced',random_state=0),
      'Gradient boosting':HistGradientBoostingClassifier(learning_rate=.05,max_depth=4,l2_regularization=1.0,class_weight='balanced',random_state=0),
      'Majority-class baseline':DummyClassifier(strategy='most_frequent')}

def fit_bayesian_network(train,topology='baseline',strict_remove=None):
    from pgmpy.models import DiscreteBayesianNetwork
    from pgmpy.estimators import BayesianEstimator
    edges=build_edges(topology)
    if strict_remove:
        edges=[e for e in edges if strict_remove not in e]
    model=DiscreteBayesianNetwork(edges)
    cols=list(model.nodes())
    fit=train[cols].copy()
    for c in cols: fit[c]=fit[c].astype(str)
    state_names={c:STATES[c] for c in cols}
    estimator=BayesianEstimator(model,fit,state_names=state_names)
    model.add_cpds(*estimator.get_parameters(prior_type='BDeu',equivalent_sample_size=10))
    return model

def main():
    p=argparse.ArgumentParser(description='Reference implementation of the final model protocol')
    p.add_argument('--show-edges',action='store_true')
    p.add_argument('--show-class-balance',action='store_true')
    args=p.parse_args()
    raw=pd.read_csv(ROOT/'data/simulation/fem_dataset_528.csv')
    d=add_fixed_targets_and_design(raw)
    if args.show_edges:
        for a,b in build_edges(): print(f'{a} -> {b}')
    if args.show_class_balance:
        for t in TARGETS: print(t, d[t].value_counts().to_dict())
    if not (args.show_edges or args.show_class_balance):
        print('Reference protocol loaded.')
        print('Use --show-edges or --show-class-balance, or import this module for model recomputation.')
        print('Canonical manuscript outputs are archived under results/.')

if __name__=='__main__': main()
