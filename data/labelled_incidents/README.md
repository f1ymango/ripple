# Incident Reader messages

`messages.jsonl` holds real Special Traffic News messages from the Transport
Department, taken from the DATA.GOV.HK historical archive. Attribute
DATA.GOV.HK and the Transport Department wherever they are shown.

Made with:

    python -m src.reader.sample --start 2026-09-15 --end 2026-09-21 --n 20 --seed 42 \
        --out data/labelled_incidents/messages.jsonl

That week had 674 archived snapshots, 334 distinct messages and 168 incidents.
Each line is `{"archive_time": "YYYYMMDD-HHmm", "stn": {every feed field, as text}}`,
one message per incident.

**These 20 are the dev set.** Read them freely while working on the prompt.
The ~100 hand-labelled messages behind the accuracy number (the gold set,
`gold_messages.jsonl` and `gold_labels.jsonl`) must not include any of these
incidents, so the prompt was never tuned on them. How the gold set is made,
labelled and scored: [LABELLING.md](LABELLING.md).

The prompt's worked examples are messages 146439, 146525, 146509, 146286
and 146213 (none from these 20 incidents). Keep them out of the labelled set
too.

None of the 20 is on the Aberdeen corridor; the whole week had only two
corridor incidents (IN-26-06874, IN-26-06904). Corridor messages need to be
sought out deliberately from a longer window.
