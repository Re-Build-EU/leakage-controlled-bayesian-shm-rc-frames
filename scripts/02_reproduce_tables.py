#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'generated/tables'; OUT.mkdir(parents=True,exist_ok=True)

# Leakage effect
pd.read_csv(ROOT/'results/repeated_cv/leakage_effect.csv').to_csv(OUT/'table_leakage_effect.csv',index=False)

# Leakage-controlled model comparison
r=pd.read_csv(ROOT/'results/repeated_cv/repeated_summary.csv')
r[r.Regime=='controlled'][['Target','Model','Accuracy','AccuracySD','MacroF1','MacroF1SD']].to_csv(OUT/'table_model_comparison_controlled.csv',index=False)

# Strict same-scalar
s=pd.read_csv(ROOT/'results/sensitivity/strict_leakage/strict_summary.csv')
a=pd.read_csv(ROOT/'results/sensitivity/strict_leakage/strict_agreement.csv')
s.merge(a,on='Target',how='left').to_csv(OUT/'table_strict_same_scalar.csv',index=False)

# Topology sensitivity
pd.read_csv(ROOT/'results/sensitivity/topology/topology_summary.csv').to_csv(OUT/'table_topology_sensitivity.csv',index=False)

# Calibration
pd.read_csv(ROOT/'results/calibration/posterior_calibration.csv').to_csv(OUT/'table_posterior_calibration.csv',index=False)

# Geometry transfer wide table
l=pd.read_csv(ROOT/'results/geometry_transfer/logo_by_geometry.csv')
l['Accuracy_MacroF1']=l.apply(lambda x:f"{x['Accuracy']:.3f} / {x['MacroF1']:.3f}",axis=1)
w=l.pivot(index='HeldOutGeometry',columns='Target',values='Accuracy_MacroF1').reset_index()
w.to_csv(OUT/'table_leave_one_geometry_out.csv',index=False)

# Experimental table
ex=pd.read_csv(ROOT/'data/experimental/experimental_evidence_and_posteriors.csv')
cols=['Specimen','maximum_interstory_drift_ratio','StructuralConfigurationClass','P_significant_damage','P_substantial_stiffness_loss','P_retained_residual_capacity']
ex[cols].to_csv(OUT/'table_experimental_posteriors.csv',index=False)

# Sensitivity tables
pd.read_csv(ROOT/'results/sensitivity/thresholds/label_agreement.csv').to_csv(OUT/'table_threshold_sensitivity.csv',index=False)
pd.read_csv(ROOT/'results/sensitivity/hinge_length/hinge_length_summary.csv').to_csv(OUT/'table_hinge_length_sensitivity.csv',index=False)
print('Wrote manuscript-support tables to',OUT)
