# Rejected synthetic F drafts — 13 October 2026

`mock_genai_briefing_20261013_token_a.json` and
`mock_genai_briefing_20261013_token_b.json` are saved outputs of bounded local
Qwen3:8b fixture calls. They passed the structural schema and token checks,
but **both failed semantic review**. They are not gold examples, accepted
briefings, real-incident output or public presentation copy.

- `token_a`: unsupported congestion and emergency-travel-time effect claims;
  public/sign text asks drivers to review rather than giving usable candidate
  route guidance.
- `token_b`: unsupported worsening-travel-time and audience claims; the
  Traditional Chinese sign text corrupts a route name.

The source fixture metrics are synthetic. Exact calls and hashes are in
[`evidence/ai-log/2026-10-13.jsonl`](../../evidence/ai-log/2026-10-13.jsonl)
and [`docs/lead-genai-follow-up-2026-10-13.md`](../../docs/lead-genai-follow-up-2026-10-13.md).
