# Scope and related work

## Scope

This package models three specific systems from *GoldenEye* (1995) with
closed-form, deterministic approximations. It is engineering mission software,
not a predictive defence-physics code, and its honesty about assumptions is
part of the deliverable.

**EMP envelope.** The ground field is a *conservative point-source envelope*.
It omits the full distributed-source HEMP field computation, polarization and
coupling detail, and site-specific shielding/cable-coupling response. Because
it treats the source as a point, the kill footprint it yields is smaller than
a detailed code would predict — deliberately the conservative direction for a
damage assessment. Waveform components E1/E2/E3 use documented representative
rate constants; E2 is not standardized (IEC defines E1 most strictly) and its
amplitude fraction is an engineering default.

**Kill radius.** Vulnerability-class thresholds are engineering references
from the EMP-hardening literature (e.g. MIL-STD-188-125 for the 50 kV/m E1
hardness level), not guarantees for specific equipment under specific coupling
conditions. Damage probability is a smooth surrogate, not a validated
reliability model.

**Dam breach.** The Ritter solution assumes an instantaneous, complete breach
on a dry, frictionless, prismatic bed. Real dam failures evolve over minutes
with friction and valley geometry, so arrival times here are lower bounds and
depths are idealizations. The Froehlich regression is a statistical peak-
outflow relation and carries scatter. The breach hydrograph is a
volume-conserving triangular idealization of a real, irregular outflow curve;
the downstream station table uses the frictionless asymptotic peak depth
`4H/9` rather than a full flood-routing model.

**Orbital platform.** The orbital analysis assumes a circular, two-body orbit
(Bate, Mueller & White) and a directly-overhead pass for the pass-duration
approximation; it ignores J2 perturbations, drag, and a real, non-zenith pass
profile, so durations are upper-bound estimates of a usable detonation window.

**Coupling and shielding.** Coupling uses a simple effective-height model of
an exposed conductor (Ott; Vance) and the plane-wave Schelkunoff approximation
for shielding; it omits the multiple-reflection correction, aperture/cable
penetration leakage, and non-plane-wave (diffuse) coupling. Induced voltages
are open-circuit estimates, not load- and joint-dependent.

**Grid resilience.** Survival probabilities assume independent asset failures
from the local envelope field; the expected served load is the sum of each
critical load's best-path reliability (an independence approximation, not a
full stochastic cascade). The canonical 5-node network is a scenario dataset,
not the real Severnaya grid.

## Related work

The models sit on well-established foundations. High-altitude EMP is treated
in the canonical reference *The Effects of Nuclear Weapons* (Glasstone and
Dolan, 1977), and the early-time waveform shape follows IEC 61000-2-9.
Orbital mechanics follow Bate, Mueller & White's *Fundamentals of
Astrodynamics* (1971). Coupling and shielding follow Ott's *Electromagnetic
Compatibility Engineering* (2009) and Vance's *Coupling to Shielded Cables*
(1975). Peak dam-breach outflow is regressed by Froehlich (1995) and breach
geometry by Froehlich (2008); the classical instantaneous dam-break solution
originates with Ritter (1892) and is presented textually in Stoker's *Water
Waves* (1957). Network-resilience reasoning draws on the deterministic
reliability and max-flow literature, and on the cascade-failure framing of
Buldyrev et al. (2010). Defense-in-depth detection probability is the
standard layered-reliability formula. The BOND protocol itself is specified in
the frozen `bond-api` package; this package is one of many films implementing
that contract.
