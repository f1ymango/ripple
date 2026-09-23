# Deck and evidence pack

Owner: Impact. The pitch is five minutes, then five to seven minutes of
questions, and the deck is preloaded by the organisers. Narrative, evidence,
Q&A and the ethics material live in [docs/05-pitch.md](../docs/05-pitch.md);
this folder holds the deck itself and the evidence behind it.

## The five criteria, 20% each

Every slide should be traceable to one of these. Three of the five belong to
this component.

| Criterion | Owner | Where the material comes from |
|---|---|---|
| Convincing framing of problem | Impact | `docs/05-pitch.md` §1, §3 |
| Prototype / demo | Visuals + Lead | the video, the console |
| Appropriate technical component | Lead | the three GenAI jobs, measured Reader accuracy |
| Feasibility and impact | Impact | `docs/05-pitch.md` §6, plus the costing below |
| Sustainability and ethics | Impact | `docs/05-pitch.md` §5, the constraint thresholds |

## What goes in here

- `deck.pdf` / the slides themselves, once they exist
- `costing.md` — what it costs to run one corridor for a year, and what a
  prevented delay is worth. Cost: compute, storage, maintenance hours. Benefit:
  vehicle-hours of delay avoided (from `results/`) × a Hong Kong value of time,
  giving dollars per incident and a benefit–cost ratio we can set beside the
  10:1–25:1 that the US corridor studies report. Name the source of every
  figure; where no source exists, say so rather than estimating.
- `real-vs-simulated.md` — an honest table of what works today and what is
  simulated, kept current as the repo changes. The prototype criterion asks
  this outright.
- `qa-sheet.md` — every question a judge might ask, with the teammate who
  answers it. Start from `docs/05-pitch.md` §4 and extend. Nobody's question
  should be unowned.

## Rules that apply here too

- Every number traces to a file in `results/` or to a cited source with the date
  it was checked. Nothing is estimated to fill a gap.
- If a figure is not measured yet, write "not measured yet" on the slide. An
  honest gap survives the Q&A; an invented number does not.

## Dates

| Date | What |
|---|---|
| Sat 3 Oct | Interim report submitted (official deadline Sun 4 Oct) |
| Wed 14 Oct | Results freeze — every number in the deck is locked |
| Sat 17 Oct | Deck and prototype submitted (official deadline Sun 18 Oct) |
| Sat 24 Oct | Final pitch, CityU Kowloon Tong |
