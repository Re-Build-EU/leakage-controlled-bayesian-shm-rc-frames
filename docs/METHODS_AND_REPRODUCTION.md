# Methods and reproduction specification

This document defines the computational quantities used by the released dataset and analysis records.

## Nonlinear finite-element response population

The RC frames were modelled in OpenSees/OpenSeesPy using force-based `beamWithHinges` elements. Nonlinear fiber sections were assigned at the member ends and elastic interior regions were retained. Concrete and reinforcement were represented using Concrete02 and Steel02, respectively. The nonlinear-region length was set to 0.10 of the corresponding member dimension (column height or beam span). P-Delta transformation was used for columns and Linear transformation for beams. Gravity loads were applied first and retained during the subsequent monotonic displacement-controlled pushover analysis. Floor lateral forces were proportional to floor level. Alternative Newton-based solution procedures were used when necessary to trace degrading response.

The released response dataset is the canonical starting point for the SHM/ML analyses. OpenSees solver behavior can vary by platform and solver build; therefore the archived dataset and fold-level outputs are provided to make the article's numerical results auditable independently of a complete 528-case FE rerun.

## Target-defining quantities

### Maximum interstory drift

For the set of converged pushover steps S and the set of column elements C,

`theta_max = max_{s in S, e in C} |u_j,e(s) - u_i,e(s)| / h_e`

where `h_e` is the actual vertical height of column `e`. The diagnostic damage classes are:

- none: theta < 0.005
- minor: 0.005 <= theta < 0.010
- moderate: 0.010 <= theta < 0.020
- severe: theta >= 0.020

### Fractional secant stiffness loss

`D_K = 1 - K_end / K_0`

`K_0` is the secant slope at the fifth saved converged pushover point and `K_end` is the secant slope at the final available converged response point. Classes:

- low: D_K < 0.60
- medium: 0.60 <= D_K < 0.80
- high: D_K >= 0.80

### Postpeak strength retention

`R_V = V_end / V_max`

Classes:

- retained: R_V >= 0.80
- failed: R_V < 0.80

## Member response descriptor

Section curvature is obtained directly from the nonlinear integration sections. The column-to-beam curvature ratio is

`R_CB^kappa = max |kappa_column| / (max |kappa_beam| + epsilon)`

with the maxima taken over nonlinear integration sections and available pushover steps. Larger values indicate relatively greater column curvature demand. For inference, the continuous ratio is categorized by training-partition tertiles; it is not treated as a deterministic beam/column failure boundary.

## Diagnostic evidence groups

### Design descriptors — fixed categorization

- concrete strength class: low < 30 MPa; medium 30-<36 MPa; high >= 36 MPa
- steel yield class: low < 430 MPa; medium 430-<470 MPa; high >= 470 MPa
- column section class: based on gross area, low < 160000 mm^2; medium 160000-<210000 mm^2; high >= 210000 mm^2
- beam section class: based on gross area, low < 140000 mm^2; medium 140000-<190000 mm^2; high >= 190000 mm^2
- gravity load level: low < 200 kN/node; medium 200-<260 kN/node; high >= 260 kN/node
- structural configuration class: derived from geometry family and regular/stilted configuration

### Mechanism descriptors — training-partition tertiles

- normalized early lateral deformation: `roof_disp_at_80Vmax_mm / (H_mm * n_stories)`
- member response regime: `R_CB^kappa`

### Response descriptors

- maximum interstory drift class: fixed damage-state thresholds
- base shear class: training-partition tertiles
- column section curvature class: training-partition tertiles
- beam section curvature class: training-partition tertiles
- stiffness degradation class: fixed stiffness-loss thresholds
- postpeak strength retention class: fixed residual-capacity threshold

Empirical tertile thresholds are estimated from the training partition only and applied unchanged to the held-out partition.

## Same-scalar leakage control

The target-specific same-scalar descriptor is omitted from observed inference evidence for the corresponding target:

- DamageState: withhold maximum interstory drift class
- StiffnessLoss: withhold stiffness degradation class
- ResidualCapacity: withhold postpeak strength retention class

The node remains in the fitted Bayesian network in the primary leakage-controlled analysis. The strict sensitivity analysis removes the same-scalar node and all incident edges before Bayesian parameter learning.

## Bayesian network

The network is an expert-specified directed acyclic graph. Main dependencies are:

1. each design descriptor -> DamageState and StiffnessLoss;
2. EarlyDeformationClass -> DamageState;
3. MemberResponseRegime -> DamageState, StiffnessLoss, ResidualCapacity;
4. DamageState -> StiffnessLoss;
5. DamageState and StiffnessLoss -> each response descriptor;
6. MemberResponseRegime, DamageState, StiffnessLoss, and all response descriptors -> ResidualCapacity.

Conditional probability distributions are estimated using Bayesian parameter learning with a Bayesian Dirichlet equivalent uniform prior and equivalent sample size 10. Posterior inference is performed by variable elimination.

## Benchmark classifiers

- multinomial logistic regression: C = 0.5, class balancing;
- random forest: 300 trees, class balancing;
- histogram-based gradient boosting: learning rate 0.05, maximum depth 4, L2 regularization 1.0, class balancing;
- majority-class baseline.

The primary internal validation is repeated stratified five-fold cross-validation with three repetitions. Empirical discretization and all preprocessing are fit using training data only. Leave-one-geometry-out validation excludes one complete geometry family at a time.

## Calibration

Bayesian posterior calibration is evaluated from pooled out-of-fold predictions using ten equal-width confidence bins, multiclass Brier score, and expected calibration error (ECE).
