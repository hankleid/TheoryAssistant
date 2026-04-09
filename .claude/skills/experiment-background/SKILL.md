---
name: experiment-background
description: "Reference knowledge about the V_Si cavity QED experiment: system, data file, optical transitions, possible physics."
---
**Analysis goals**
- Which physical models best describe the data?
- Is strong coupling present?
- What is coupling "g" for this emitter-cavity system?

**What is known about the experimental system:**
- We are measuring a SINGLE SiC color center (independently verified with a g(2) measurement.)
- The color center is the V_Si defect (consider only cubic k-V_Si), emission at ~916 nm.
- The V_Si has two optical transitions, one for the spin-1/2 state and one for the spin-3/2 state, separated by 1.075 GHz.
- The color center is embedded in a ring resonator with two counter propagating modes. But the lifetime measurement is measured through one mode.
- The cavity has quality factor Q = 7.21e5 (721,000).

**Information about the experiment:**
- This measurement is a time-resolved lifetime measurement. X-axis is time bin and Y-axis is counts.
- The excitation peak is present in the data, followed by the decay.
- The measurement was integrated over X seconds.


**Problem statement**
Although we are certain to be measuring only one emitter, the lifetime data is not represented by a single exponential decay. Rather, there exists a kink, or bend, in the lifetime decay which indicates interesting physics may be present.

The resulting lifetime measurement is in `experimental_data/lifetime_data.dat`. We preprocessed the data for you in `load_timeresolved_data`, so the onset of the excitation (start of the rise) is at t=0.

**Additional considerations**
- Spectral diffusion may be present in this system, but the rate of spectral diffusion is unknown.
- If a stable emitter is strongly coupled to a cavity, we would expect to see Rabi oscillations in the lifetime trace.

There are many possible explanations for the interesting lifetime decay shape, especially because you only have one measurement to base your analysis on. This requires you to not only generate an exploratory list of possible Hamiltonian/Lindbladian systems to describe the system, but also creative ways of testing your hypothesis for each model.
