# Vancomycin steady-state PK simulator

A one-compartment, first-order, repeated IV infusion simulator for **educational and research use**. Estimates theoretical steady-state peak, trough, selected post-infusion concentration, 24-hour AUC, clearance, and elimination half-life from user-supplied PK parameters.

**Not a clinical dosing tool.** It does not infer renal function, fit drug concentration measurements, perform Bayesian estimation, model distribution phases, or recommend dosing. Stable PK and previously estimated elimination rate and volume are assumed.

## Browser application

The static simulator is in [`web/index.html`](web/index.html) and [`web/pk.mjs`](web/pk.mjs). It can be hosted on GitHub Pages or any static host, with no backend. The live Pages URL will be added here after deployment is verified.

To use locally, from the repository root:

```bash
python -m http.server 8000 --directory web
```

Open `http://localhost:8000/`. Enter a hypothetical dose (mg), dosing interval (h), infusion duration (h), elimination rate (h⁻¹), volume of distribution (L), and optional sample time after infusion completion (h). Select **Calculate** to see the results and a one-interval concentration curve. CSV export contains only the entered numerical inputs and calculated outputs.

The browser app uses JavaScript without third-party packages, external calculation services, cookies, or persistent storage. Do not enter patient identifiers.

## Python calculations

Python 3.10+ is sufficient for the core calculator:

```bash
python vanco_pk.py single --dose-mg 1000 --interval-h 12 --infusion-h 1 --elimination-rate-h 0.1 --volume-l 50
python vanco_pk.py batch -i sample.csv -o results.csv
```

The example predicts an AUC24 of 400 mg·h/L, end-of-infusion peak of approximately 27.24 mg/L, and predose trough of approximately 9.07 mg/L. These are synthetic PK assumptions, not patient values.

The batch CSV must contain `dose_mg`, `interval_h`, `infusion_h`, `elimination_rate_h`, and `volume_l`; `sample_after_infusion_h` is optional. Malformed input stops the batch before results are written. Unsafe spreadsheet formula prefixes in retained input text are escaped. Avoid identifiable clinical data.

### Model

For infusion duration `T`, interval `tau`, dose `D`, first-order elimination constant `k`, and apparent volume `V`:

- `CL = k × V`.
- `Cpeak,ss = [D / (T × CL)] × [ (1 − exp(−kT)) / (1 − exp(−k tau)) ]`.
- `Ctrough,ss = Cpeak,ss × exp(−k(tau − T))`.
- `AUC24 = 24 D / (tau × CL)`.
- `t½ = ln(2)/k`.

An optional modeled sample is `Cpeak,ss × exp(−k t)` for `t` hours after infusion completion, before the next dose. The calculations assume repeated identical infusions and immediate distribution into one compartment. They do not establish that a patient has reached steady state.

## Additional components

The repository retains an independent **demonstration-only** supervisor/agent suite (`agents/`, `cli.py`) with generic operational rules; these rules are **not validated clinical vancomycin thresholds**. `enrichment.py` contains conceptual threshold-based placeholders, **not** working Bayesian, two-compartment, renal dose, or target-attainment implementations.

Optional API dependencies:

```bash
python -m pip install "fastapi>=0.115,<1" "uvicorn>=0.30,<1" "pydantic>=2,<3"
python cli.py serve
```

API routes include `GET /health`, `GET /metrics` (JSON), `POST /api/pk`, and demonstration-only `/api/audit`, `/api/chat`, `/api/audit/logs`. The mock chat provider is not a clinical verification service. The audit-chain HMAC is held in memory with an ephemeral random key unless `AUDIT_SECRET_KEY` is configured. The regex identifier guard is best-effort and does **not** guarantee HIPAA de-identification.

## Tests

```bash
python -m pip install "pytest>=8,<10" "fastapi>=0.115,<1" "pydantic>=2,<3"
python -m pytest -q
node --test web/pk.test.mjs
```

Python tests exercise equations, edge cases, safe CSV handling, and existing agent behavior. Node.js 22+ runs the browser calculation unit tests. The site is designed for current Chromium, Firefox, and Safari releases that support JavaScript modules.

## Clinical context

The [2020 ASHP/IDSA/PIDS/SIDP consensus guidance](https://www.idsociety.org/practice-guideline/vancomycin/) supports AUC-guided vancomycin monitoring for serious MRSA infections, using an AUC24/MIC target of 400–600 assuming MIC = 1 mg/L. Trough-only targets of 15–20 mg/L are no longer recommended for that indication. This simulator does **not** determine target attainment or individualize therapy.

## License

[MIT](LICENSE).
