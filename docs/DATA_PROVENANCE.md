# Data provenance

## 1. Simulation population

The 528-case finite-element population was generated as a controlled structural population for post-earthquake condition-inference research. It spans regular full-scale frames, regular laboratory-scale frames, and vertically irregular stilted frames, with systematic variation in geometry, material properties, member proportions, gravity demand, and target deformation demand.

The simulation population is not intended to represent a statistically sampled building stock. Ageing, corrosion-induced reinforcement deterioration, pre-existing cracking, cyclic deterioration, ground-motion variability, and dynamic amplification are outside its scope.

The canonical dataset in this repository is `data/simulation/fem_dataset_528.csv`.

## 2. Experimental information

No new physical experiment is claimed by this repository. The experimental demonstration uses previously published test information:

- EF and RF: Wahab AG, Zhong T, Wei F, et al., Asian Journal of Civil Engineering, 2023, DOI 10.1007/s42107-023-00794-z.
- DJ-1 and DJ-2: Li R, Liu L, Li Y, et al., Journal of Earthquake Engineering, 2023, DOI 10.1080/13632469.2023.2287136.

Only processed values required by the present inference demonstration are released here. Original article text, photographs, publisher figures, and raw records are not redistributed.

## 3. Source-supported experimental assignments

For EF and RF, the published ultimate roof displacements of approximately 102.1 mm and 57.2 mm over a total specimen height of 2400 mm correspond to global roof-drift ratios of approximately 4.25% and 2.38%. These are used as lower bounds supporting the severe interstory-drift class; no unreported exact maximum story drift is invented.

For DJ-1 and DJ-2, the source reports maximum positive interstory drift angles at failure of approximately 1/22 and 1/20, corresponding to about 4.55% and 5.00%.

The processed evidence table leaves unavailable evidence unobserved. The experimental demonstration is therefore a coarse simulation-to-experiment consistency assessment, not a claim of comprehensive external validation.
