# Lead follow-up — 30 September 2026

These are copy-ready notes for the Lead to send. They have not been posted to
the team chat. PR #35 was reviewed at `037a4bc`; its focused tests pass (17).

## To Data — fallback review before merging PR #35

Thanks for getting the fallback running. I reviewed the implementation and
saved replay. Please address these before we merge and use the interim wording:

1. Separate no-closure calibration from incident replay. `run.py` injects the
   partial closure at 08:54 but scores through 08:55, so the final scored bin
   contains the intervention. Use a no-closure run for the 07:55–08:55 calibration
   comparison, then run the incident separately. Regenerate the saved artifacts;
   retain both assumptions and do not move the observed onset just to fit the score.
2. Replace “speed floor” / “cannot beat it” with “ordinary-day constant-speed
   reference.” The implementation uses a detector's mean speed over the ordinary
   hour, not a mathematical lower bound on achievable error. Equality at one
   decimal place does not prove zero model error; AID01104 is already 9.3%
   model MAPE versus 9.8% reference in the saved table. The inside-chain result
   (17.8% over 252 speed bins) misses the approximately 15% target.
3. Label 08:54 slow-lane and 09:00 all-lane closures as Data's retrospective
   hypotheses. Low flow does not establish the physical lane or closure time.
   Keep TD's 09:01 / 09:36 reports and the earlier 08:55 physical-onset proposal
   visible. The operator cannot act using later observations.
4. Restrict the current CLI to the implemented 15 May incident, or accept an
   explicit scenario configuration. `--day` currently accepts any date but still
   injects the 15 May phases and reads the fixed 15 May lane-evidence file.

Please headline the inside-chain count result (97.1% of 205 bins in the current
artifact); the 242-bin result also includes the four detectors used to supply
demand. The four chains remain unconnected for plan diversion, and the incident
queue/recovery is not yet validated. The fallback is useful progress, but the
current result is not an accepted full incident P0.

## To Data/E — approved result provenance handoff

The Lead approved an additional sidecar on 30 Sep. Each evaluator result needs
`<run_id>.provenance.json` alongside it. The existing `plan.json` and
`result.json` field shapes stay unchanged. The implementation and exact fields
are in `src/evaluation_provenance.py` and `docs/03-architecture.md`.

Call `capture_inputs` before simulation with the validated plan, D's saved
`generation-inputs.json` and the shared network/demand/incident/model-version
input files. After computing metrics, call `write_result`. F checks the hashes
and rejects stale plans, edited results, missing provenance or mixed simulation
inputs. Please integrate this when implementing E; do not retrospectively
assert hashes for old runs whose inputs were not retained.

## To Simulation

Please compare Data's fallback and the next SUMO diagnostic on the same
no-closure window and disclose count/speed denominators. The fallback's speed
reference is an ordinary-day mean, not an accepted revision of our target.
Please keep demand/network/detector placement work separate from deciding the
full-incident closure phases. We still need an explicit full P0 timing and lane
assumption, and a replay showing queue recovery before comparing interventions.

## To Impact and Visuals

The Lead's contribution is in `docs/interim-report.md`. Reader v1 is the
held-out result; v2 is a development result after prompt and label changes.
The new D/F path has offline tests, but no real evaluated plan benefits yet.
Please do not present PR #35's speed-reference comparison as proof that the
validation target is unattainable or that full P0 is accepted. Continue the
observed-data playback while simulation validation proceeds.

## Lead status

PR #34 now rejects zero-second signal interventions and common worded numeric
claims, and implements the approved provenance check. Free-form language still
needs semantic review: the numeric guard is not a complete proof that every
possible paraphrase is grounded. All publication remains subject to human review.
PR #35 should remain open until the scoring, evidence wording and scenario
scope issues above are addressed. No generated results were edited for this review.
