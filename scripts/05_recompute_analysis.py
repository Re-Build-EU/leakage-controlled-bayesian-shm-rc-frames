#!/usr/bin/env python3
"""End-to-end recomputation utility for the released SHM analysis protocol.

This script imports the final evidence and topology definitions from
04_reference_model_protocol.py and can recompute repeated stratified validation,
leave-one-geometry-out validation, strict same-scalar removal, and topology
sensitivity. It writes outputs to `recomputed/` and does not overwrite the
canonical archived results under `results/`.

Requirements: `pip install -r requirements-model.txt`
"""
from __future__ import annotations
import argparse
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import RepeatedStratifiedKFold

ROOT = Path(__file__).resolve().parents[1]
PROTO_PATH = Path(__file__).with_name('04_reference_model_protocol.py')
spec = importlib.util.spec_from_file_location('protocol', PROTO_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f'Cannot load {PROTO_PATH}')
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)


def macro_f1(y_true, y_pred, target):
    return f1_score(y_true, y_pred, labels=P.STATES[target], average='macro', zero_division=0)


def bn_predict(model, test, target, evidence_cols):
    from pgmpy.inference import VariableElimination
    infer = VariableElimination(model)
    states = P.STATES[target]
    pred, conf, probs = [], [], []
    available = set(model.nodes())
    cols = [c for c in evidence_cols if c in available]
    for _, row in test.iterrows():
        evidence = {c: str(row[c]) for c in cols if pd.notna(row[c])}
        q = infer.query([target], evidence=evidence, show_progress=False)
        names = list(q.state_names[target])
        vals = np.asarray(q.values, dtype=float)
        full = {s: 0.0 for s in states}
        for s, v in zip(names, vals):
            full[str(s)] = float(v)
        vector = np.array([full[s] for s in states], dtype=float)
        k = int(np.argmax(vector))
        pred.append(states[k]); conf.append(float(vector[k])); probs.append(vector)
    return pred, np.asarray(conf), np.asarray(probs)


def encoded(train, test, cols):
    a = pd.get_dummies(train[cols].astype(str), columns=cols)
    b = pd.get_dummies(test[cols].astype(str), columns=cols)
    return a, b.reindex(columns=a.columns, fill_value=0)


def prepare_fold(base, train_idx, test_idx):
    tr = base.iloc[train_idx].copy(); te = base.iloc[test_idx].copy()
    thr = P.learn_tertiles(tr)
    return P.apply_foldwise_evidence(tr, thr), P.apply_foldwise_evidence(te, thr)


def evaluate_fold(tr, te, target, regime='controlled', topology='baseline', strict=False, include_benchmarks=True):
    same = P.SAME_SCALAR[target]
    model = P.fit_bayesian_network(tr, topology=topology, strict_remove=(same if strict else None))
    ev = P.evidence_for(target, regime)
    if strict:
        ev = [c for c in ev if c != same]
    y = te[target].astype(str).to_numpy()
    yp, conf, probs = bn_predict(model, te, target, ev)
    out = [{
        'Model':'Bayesian network','Accuracy':accuracy_score(y,yp),
        'MacroF1':macro_f1(y,yp,target),'MeanConfidence':float(np.mean(conf))
    }]
    if include_benchmarks and not strict:
        Xtr, Xte = encoded(tr, te, ev)
        for name, clf in P.benchmark_models().items():
            clf.fit(Xtr, tr[target].astype(str))
            p = clf.predict(Xte)
            out.append({'Model':name,'Accuracy':accuracy_score(y,p),'MacroF1':macro_f1(y,p,target),'MeanConfidence':np.nan})
    return out, np.asarray(yp), conf, probs


def run_repeated(base, outdir):
    fold_rows=[]; oof_rows=[]
    for target in P.TARGETS:
        split = RepeatedStratifiedKFold(n_splits=5,n_repeats=3,random_state=42)
        for regime in ['full','controlled']:
            for fold_no,(tri,tei) in enumerate(split.split(base,base[target]), start=1):
                rep=(fold_no-1)//5+1; fold=(fold_no-1)%5+1
                tr,te=prepare_fold(base,tri,tei)
                metrics,yp,conf,probs=evaluate_fold(tr,te,target,regime=regime,include_benchmarks=True)
                for m in metrics:
                    fold_rows.append({'Target':target,'Regime':regime,'Model':m['Model'],'Repeat':rep,'Fold':fold,
                                      'NTrain':len(tr),'NTest':len(te),'Accuracy':m['Accuracy'],'MacroF1':m['MacroF1']})
                if regime=='controlled':
                    states=P.STATES[target]
                    y=te[target].astype(str).to_numpy()
                    for j,case_i in enumerate(tei):
                        r={'Target':target,'Repeat':rep,'Fold':fold,'CaseIndex':int(case_i),
                           'TrueClass':y[j],'Prediction':yp[j],'Confidence':float(conf[j])}
                        for k,s in enumerate(states): r[f'P_{s}']=float(probs[j,k])
                        oof_rows.append(r)
    folds=pd.DataFrame(fold_rows)
    folds.to_csv(outdir/'repeated_fold_level.csv',index=False)
    summary=folds.groupby(['Target','Regime','Model'],as_index=False).agg(
        Accuracy=('Accuracy','mean'),AccuracySD=('Accuracy','std'),MacroF1=('MacroF1','mean'),MacroF1SD=('MacroF1','std'))
    summary.to_csv(outdir/'repeated_summary.csv',index=False)
    pd.DataFrame(oof_rows).to_csv(outdir/'bn_oof_posteriors.csv',index=False)


def run_logo(base, outdir):
    rows=[]
    for target in P.TARGETS:
        for fam in sorted(base.GeometryFamily.unique()):
            tri=np.flatnonzero(base.GeometryFamily.to_numpy()!=fam); tei=np.flatnonzero(base.GeometryFamily.to_numpy()==fam)
            tr,te=prepare_fold(base,tri,tei)
            metrics,_,_,_=evaluate_fold(tr,te,target,regime='controlled',include_benchmarks=False)
            m=metrics[0]
            rows.append({'Target':target,'HeldOutGeometry':fam,'NTrain':len(tr),'NTest':len(te),'Accuracy':m['Accuracy'],'MacroF1':m['MacroF1'],'MeanConfidence':m['MeanConfidence']})
    d=pd.DataFrame(rows); d.to_csv(outdir/'logo_by_geometry.csv',index=False)
    d.groupby('Target',as_index=False).agg(LOGOAccuracy=('Accuracy','mean'),LOGOAccuracySD=('Accuracy','std'),LOGOMacroF1=('MacroF1','mean'),LOGOMacroF1SD=('MacroF1','std')).to_csv(outdir/'logo_summary.csv',index=False)


def run_strict(base, outdir):
    rows=[]
    for target in P.TARGETS:
        split=RepeatedStratifiedKFold(n_splits=5,n_repeats=3,random_state=42)
        for fold_no,(tri,tei) in enumerate(split.split(base,base[target]),start=1):
            rep=(fold_no-1)//5+1; fold=(fold_no-1)%5+1
            tr,te=prepare_fold(base,tri,tei)
            for strict,name in [(False,'Inference-only withholding'),(True,'Strict node removal and refit')]:
                metrics,_,_,_=evaluate_fold(tr,te,target,regime='controlled',strict=strict,include_benchmarks=False)
                m=metrics[0]
                rows.append({'Target':target,'Method':name,'Repeat':rep,'Fold':fold,'Accuracy':m['Accuracy'],'MacroF1':m['MacroF1'],'MeanConfidence':m['MeanConfidence']})
    d=pd.DataFrame(rows); d.to_csv(outdir/'strict_fold_level.csv',index=False)
    d.groupby(['Target','Method'],as_index=False).agg(Accuracy=('Accuracy','mean'),AccuracySD=('Accuracy','std'),MacroF1=('MacroF1','mean'),MacroF1SD=('MacroF1','std'),MeanConfidence=('MeanConfidence','mean')).to_csv(outdir/'strict_summary.csv',index=False)


def run_topology(base, outdir):
    rows=[]; tops=['baseline','early_deformation_to_stiffness','no_damage_to_stiffness','mediated_residual']
    for target in P.TARGETS:
        split=RepeatedStratifiedKFold(n_splits=5,n_repeats=3,random_state=42)
        splits=list(split.split(base,base[target]))
        for top in tops:
            for fold_no,(tri,tei) in enumerate(splits,start=1):
                rep=(fold_no-1)//5+1; fold=(fold_no-1)%5+1
                tr,te=prepare_fold(base,tri,tei)
                metrics,_,_,_=evaluate_fold(tr,te,target,regime='controlled',topology=top,include_benchmarks=False)
                m=metrics[0]
                rows.append({'Target':target,'Topology':top,'Repeat':rep,'Fold':fold,'Accuracy':m['Accuracy'],'MacroF1':m['MacroF1'],'MeanConfidence':m['MeanConfidence']})
    d=pd.DataFrame(rows); d.to_csv(outdir/'topology_fold_level.csv',index=False)
    d.groupby(['Target','Topology'],as_index=False).agg(Accuracy=('Accuracy','mean'),AccuracySD=('Accuracy','std'),MacroF1=('MacroF1','mean'),MacroF1SD=('MacroF1','std'),MeanConfidence=('MeanConfidence','mean')).to_csv(outdir/'topology_summary.csv',index=False)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--mode',choices=['repeated','logo','strict','topology','all'],default='all')
    ap.add_argument('--output',default='recomputed',help='Output directory relative to package root or absolute path')
    args=ap.parse_args()
    out=Path(args.output); out = out if out.is_absolute() else ROOT/out; out.mkdir(parents=True,exist_ok=True)
    base=P.add_fixed_targets_and_design(pd.read_csv(ROOT/'data/simulation/fem_dataset_528.csv'))
    if args.mode in ('repeated','all'): run_repeated(base,out)
    if args.mode in ('logo','all'): run_logo(base,out)
    if args.mode in ('strict','all'): run_strict(base,out)
    if args.mode in ('topology','all'): run_topology(base,out)
    print('Recomputed outputs written to',out)
    print('Compare these files with canonical archived records under results/.')

if __name__=='__main__':
    main()
