# Methodology

## Orbital EMP weapon model (`src/goldeneye/emp_model.py`)

A high-altitude nuclear burst (HEMP) releases a prompt gamma flux; the gammas
Compton-scatter in the atmosphere, driving a radial electron current that
radiates the early-time (E1) electromagnetic pulse. We model the ground-level
E1 peak field as a documented conservative point-source envelope:

$$E(r) = E_0 \, Y_s \, \left(\frac{h}{d}\right)^2 \exp\!\left(-\frac{d-h}{\lambda(h)}\right),$$

where $h$ is the burst altitude, $d = \sqrt{h^2 + r^2}$ the slant range to a
ground point at horizontal range $r$, $Y_s = (Y/Y_\text{ref})^{0.85}$ the
empirical yield scaling, and $\lambda(h)$ the effective gamma attenuation
length, which grows exponentially with altitude (thinner air). Reflecting the
finiteness of the deposition region, the amplitude anchor is
$E_0 = 50000$ V/m at a megaton-class reference yield, matching the canonical
HEMP figure; the prompt-gamma fraction is fixed at 0.3% (Glasstone and Dolan,
1977). Beyond line of sight the field is taken as zero, which bounds the
illuminated footprint to the geometric horizon
$\sqrt{2 R_\oplus h + h^2}$.

The package also implements the canonical waveform as a normalized
double-exponential, $E(t) = A\,k\,(e^{-\alpha t}-e^{-\beta t})$, with the
early-time (E1), intermediate-time (E2), and late-time magnetohydrodynamic
(E3) components distinguished by documented rate constants (IEC 61000-2-9 for
E1) and amplitude policies.

## Electronics kill-radius analysis (`src/goldeneye/kill_radius.py`)

Four vulnerability classes are defined by increasing damage thresholds:
*unprotected* microelectronics (~1 kV/m), *commercial*/semi-hardened
(~10 kV/m), *MIL-STD-188-125*-hardened facilities (50 kV/m), and *legacy
vacuum-tube*/relay electronics (~1 MV/m). Because the E1 envelope is monotone
decreasing in range, the kill radius — the range at which the field meets the
class threshold — is found by deterministic bisection. The enclosed kill area
is $\pi r^2$, and the fraction of the illuminated footprint covered is
$(r/r_\text{horizon})^2$. A smooth damage-probability logistic,
$P = \bigl[1+\exp(-s(E/T-1))\bigr]^{-1}$, gives $P=0.5$ exactly at the damage
threshold.

## Arkangel dam security (`src/goldeneye/dam_security.py`)

**Access control (defense in depth).** The facility is modelled as a cascade
of $n$ layers, each with a per-pass detection probability $p_i$ and response
time $t_i$. The probability of at least one detection is
$1-\prod_i(1-p_i)$; the expected response time to the first detecting layer
weights each $p_i \prod_{j<i}(1-p_j)$ by $t_i$. A composite security score
blends detection coverage with responsiveness in $[0,100]$.

**Breach flood risk.** A dam breach releases a flood wave. Peak outflow
follows the published Froehlich (1995) embankment regression (Froehlich, 1995):
$$Q_p = 0.607\, V^{0.295} H^{1.24},$$
with reservoir volume $V$ and breach head $H$ in SI units. Downstream
propagation uses the Ritter (1892) instantaneous dam-break solution on a dry,
frictionless bed (Ritter, 1892): with $c_0=\sqrt{gH}$, the depth and velocity in the
wave region $(-c_0 \le x/t \le 2c_0)$ are

$$h(x,t) = \frac{1}{9g}\left(2c_0 - \frac{x}{t}\right)^2, \qquad
u(x,t) = \frac{2}{3}\left(c_0 + \frac{x}{t}\right),$$

the front arrives at a downstream distance $x$ at time $x/(2c_0)$, and the
asymptotic peak depth at any fixed distance is $4H/9$. The facility inundation
severity is the mean depth over its ground elevation, binned into a
low/moderate/high/extreme risk rating.

## Orbital platform geometry (`src/goldeneye/orbital_mechanics.py`)

The weapon is delivered from a circular orbital platform. Keplerian kinematics
give the period $T = 2\pi\sqrt{a^3/\mu}$ and speed $v = \sqrt{\mu/a}$ for an
orbit of radius $a$ about the Earth of gravitational parameter
$\mu = 3.986\times10^{14}$ m^3/s^2 (Bate, Mueller & White, 1971). Spherical
Earth geometry yields the central angle, elevation angle, and slant range
between the ground target and the platform; a deterministic bisection finds the
maximum central angle at which a chosen minimum elevation is maintained, whose
arc fraction of the orbit bounds the usable pass duration.

## Electromagnetic coupling and shielding (`src/goldeneye/coupling.py`)

To reach electronics the field must couple onto conductors and penetrate
enclosures. Skin depth follows the classical $\delta = \sqrt{\rho/(\pi f \mu_0 \mu_r)}$.
Schelkunoff shielding effectiveness combines plane-wave absorption
$A = 8.686\,t/\delta$ dB with reflection $R = 168 - 10\log_{10}(\mu_r f/\sigma)$ dB
(Ott, *Electromagnetic Compatibility Engineering*, 2009; the multiple-reflection
correction is neglected for thick shields). An exposed conductor of length $L$
at field-elevation $\varepsilon$ has effective height $h_\mathrm{eff} =
L\sin\varepsilon$, coupling an induced voltage $V = E\,h_\mathrm{eff}$, and a
protection margin $20\log_{10}(\text{withstand}/E)$ dB quantifies residual
hardness.

## Regional power-network resilience (`src/goldeneye/grid_resilience.py`)

The regional network is a graph of nodes (plants, substations, loads) and
transmission lines on the local plane, the burst nadir at the origin. Every
asset carries a vulnerability class; its survival probability is
$1-P_\mathrm{damage}(E)$ at the asset's envelope field. The most-reliable
source-to-load route maximises the product of survival probabilities
(equivalent to shortest paths under $-\log(\text{survival})$ weights,
deterministic Dijkstra with insertion-order tie-breaking); redundancy is the
number of edge-disjoint routes via Edmonds-Karp max flow with unit capacities.
The report's expected served load assumes independence of the surviving
assets along each best path (a documented approximation).

## Breach outflow hydrograph (`src/goldeneye/breach_hydrograph.py`)

The breach's time evolution extends the dam-break analysis. The average breach
width follows the Froehlich (2008) regression
$B_\mathrm{avg} = 0.27\,K_0\,V^{0.32}H^{0.04}$ (Froehlich, 2008). The outflow is
a volume-conserving triangular hydrograph falling linearly from the Froehlich
(1995) peak discharge to zero over $t_d = 2V/Q_p$, so the discharged area
equals the stored volume; its mean outflow is $V/t_d$. A downstream station
table combines the Ritter front-arrival time, the asymptotic peak depth
$4H/9$, and the flood-risk rating at each named station.
