#!/usr/bin/env python3
from pathlib import Path
import sys
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

def check(cond, msg):
    if not cond:
        raise AssertionError(msg)

def near(a,b,tol=5e-6):
    return abs(float(a)-float(b)) <= tol

raw = pd.read_csv(ROOT/'data/simulation/fem_dataset_528.csv')
check(raw.shape == (528,41), f'Unexpected dataset shape: {raw.shape}')
check(raw['CaseID'].nunique() == 528, 'CaseID must be unique')
check(raw['CaseID'].isna().sum() == 0, 'Missing CaseID')
check(int((raw.ConvergedFully==1).sum()) == 511, 'Expected 511 fully converged cases')
check(int((raw.ConvergedFully==0).sum()) == 17, 'Expected 17 partial cases')

# final target definitions
damage = pd.cut(raw.max_story_drift_ratio, [-np.inf,.005,.01,.02,np.inf], right=False,
                labels=['none','minor','moderate','severe'])
stiff = pd.cut(raw.stiffness_loss_frac, [-np.inf,.60,.80,np.inf], right=False,
               labels=['low','medium','high'])
resid = np.where(raw.post_peak_strength_ratio < .80, 'failed', 'retained')
check(damage.value_counts().to_dict() == {'severe':295,'moderate':97,'minor':85,'none':51}, 'Damage-state counts differ')
check(stiff.value_counts().to_dict() == {'high':288,'medium':166,'low':74}, 'Stiffness-loss counts differ')
rv = pd.Series(resid).value_counts().to_dict()
check(rv == {'retained':387,'failed':141}, 'Residual-capacity counts differ')

# true interstory consistency for regular frames
reg = raw[raw.Regularity=='regular']
check(bool((reg.max_story_drift_ratio + 1e-10 >= reg.global_roof_drift_ratio).all()), 'Regular-frame ISDR/global drift consistency failure')

# repeated CV canonical values
rep = pd.read_csv(ROOT/'results/repeated_cv/repeated_summary.csv')
def rmetric(target, regime, model, col):
    x=rep[(rep.Target==target)&(rep.Regime==regime)&(rep.Model==model)]
    check(len(x)==1, f'Missing repeated result {target}/{regime}/{model}')
    return x.iloc[0][col]
for t,full,ctrl in [
    ('DamageState',.910882,.626286),('StiffnessLoss',.932809,.741342),('ResidualCapacity',.907223,.645458)]:
    check(near(rmetric(t,'full','Bayesian network','MacroF1'),full), f'{t} full BN F1')
    check(near(rmetric(t,'controlled','Bayesian network','MacroF1'),ctrl), f'{t} controlled BN F1')

# calibration
cal = pd.read_csv(ROOT/'results/calibration/posterior_calibration.csv').set_index('Target')
for t,ece in [('DamageState',.138021),('StiffnessLoss',.104445),('ResidualCapacity',.070080)]:
    check(near(cal.loc[t,'ECE'],ece), f'{t} ECE')

# LOGO
logo = pd.read_csv(ROOT/'results/geometry_transfer/logo_summary.csv').set_index('Target')
for t,f1 in [('DamageState',.500932),('StiffnessLoss',.601034),('ResidualCapacity',.551605)]:
    check(near(logo.loc[t,'LOGOMacroF1'],f1), f'{t} LOGO F1')

# strict leakage
strict = pd.read_csv(ROOT/'results/sensitivity/strict_leakage/strict_summary.csv')
def smetric(t,m,c):
    x=strict[(strict.Target==t)&(strict.Method==m)]
    check(len(x)==1,f'Missing strict result {t}/{m}')
    return x.iloc[0][c]
check(near(smetric('ResidualCapacity','Strict node removal and refit','MacroF1'),.701306), 'Strict residual F1')
agr = pd.read_csv(ROOT/'results/sensitivity/strict_leakage/strict_agreement.csv').set_index('Target')
check(near(agr.loc['ResidualCapacity','PredictionAgreement'],.830808), 'Strict residual agreement')

# topology
top = pd.read_csv(ROOT/'results/sensitivity/topology/topology_summary.csv')
def tmetric(target, topology, col):
    x=top[(top.Target==target)&(top.Topology==topology)]
    check(len(x)==1, f'Missing topology result {target}/{topology}')
    return x.iloc[0][col]
check(near(tmetric('DamageState','early_deformation_to_stiffness','MacroF1'),.613622), 'Topology damage F1')
check(near(tmetric('StiffnessLoss','no_damage_to_stiffness','MacroF1'),.679098), 'Topology stiffness F1')
check(near(tmetric('ResidualCapacity','mediated_residual','MacroF1'),.748728), 'Topology residual F1')

# experimental posterior summary
ex = pd.read_csv(ROOT/'data/experimental/experimental_posterior_summary.csv').set_index('Specimen')
expected={'EF':(.943141,.995736),'RF':(.887839,.994643),'DJ1':(.897400,.954865),'DJ2':(.897400,.954865)}
for s,(d,k) in expected.items():
    check(near(ex.loc[s,'P_significant_damage'],d), f'{s} damage posterior')
    check(near(ex.loc[s,'P_substantial_stiffness_loss'],k), f'{s} stiffness posterior')

print('PACKAGE VALIDATION: PASS')
print('Dataset:', raw.shape, '| fully converged:', int((raw.ConvergedFully==1).sum()), '| partial:', int((raw.ConvergedFully==0).sum()))
print('All key manuscript metrics match the canonical archived outputs.')
