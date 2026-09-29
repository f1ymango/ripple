# TD lane-scope cross-check

Source: DATA.GOV.HK historical archive, TD raw detector feed.
Retain raw per-period lane readings for review; sampled zero flow does not prove a lane closure.

Only the listed archive snapshots are used. Timestamps below come from the XML periods, not filenames.

| Detector | Observed periods | Lane counts | Lane sets |
|---|---:|---|---|
| AID01104 | 64 | 2 | Fast Lane / Slow Lane |

## Source snapshots

| Archive timestamp | Status | SHA-256 |
|---|---|---|
| 20260515-0841 | read | e036fd6c942a803a07bed74de810f3723d80d24048856ff110ad7bc6dc545073 |
| 20260515-0845 | read | c74968c7b8073d125e3b4d84c114c3fa3094cd8581568d47176fb44ec3d22b9f |
| 20260515-0846 | read | 9ee51e61d8292af01b59895e53645c4a8f2f25d7ec909dd008820999e88c9b4e |
| 20260515-0849 | read | 88929bb92fbb72085b3ad4be516e047109dbbf291a69dda08b73c8a5e3133c96 |
| 20260515-0850 | read | cd5fe776ab38987790ae233fd96c9e3e32649171401251495306aa9c810313b1 |
| 20260515-0851 | read | 36d8be7093b032177a78d44a6a8532ef1fc622c2982a3dbfbf20ba8232fabb42 |
| 20260515-0852 | read | 58a5a8cf14bbbbccb9093ccb3fe526cdd2757ca3459851cb5ea01dd2b8390efa |
| 20260515-0853 | read | 8d173868a879023aa1576d00fca7fec0380629cf809ecfed67dc39d57690c52f |
| 20260515-0856 | read | 082f252f613b161036f26d1ce7c0952b73236c41598364c534a103466532f28f |
| 20260515-0857 | read | b094d9e84a716886d22086905a828d30604f43adec2984a09ce7c9d638e4d51d |
| 20260515-0901 | read | cff2497d3d7fc4154b872fc69166b862cd8f8c0347412ee0b67a1d77522a4b14 |
| 20260515-0902 | read | c0e8e26b2215112c116a32242c1c84b625dbc5d60d394dd0732cb72a23dcd421 |
| 20260515-0907 | read | a4f0c1ef592a90df565c15c2dab9fe2ff864f9e5fe58ccd472a51bffd65dafaa |
| 20260515-0912 | read | 0215827d2c1c41cd0bd2156e76180df8d6eac2034dbc2dddff49f227a2a6d9d3 |
| 20260515-0916 | read | 324392d48343c7dccaa5b46445b81a5885c13fd48ece536cff39165ebe267d56 |
| 20260515-0920 | read | 24e16846678a0b2fa379109bd2964cc4cef2cc4446d84689481d80107cf398f4 |
| 20260515-0921 | read | f987d7547ec24768281946dc56286215d1d63e5f48151e7150c8de1b59158b56 |
| 20260515-0925 | read | 70d3ea0b437c03befdf33b9f6800da268c77457818b7ebabda96d3f6f9fa26d6 |
| 20260515-0927 | read | 5261c1dac236fa9d7f45bd475810265e1e62480acb5b2e19bdfffae49fdca88e |
| 20260515-0928 | read | c3055d7a9f4e1e598999c7398598f0b1ec241f778c8f28870eac7b8bec5a36b0 |
| 20260515-0930 | read | 8dcb6397d85f2a5d92bad7fe7ec4b270b22f7e279dc471f2f4d46f05a0f10d88 |
| 20260515-0931 | read | 1131d0f1a844b99caccfa5abf4c6540bfefbeb9511739e72c4070a63b226f4a2 |
| 20260515-0936 | read | 6348e04b210874aa3e97096efd9ceaf3e06a84d87f53904eb8322d6a5c2a0b94 |
| 20260515-0937 | read | e4cb63542e9744a601f9d3aff5f9f66498c9556a3b78568a9651246677c1ed5e |
| 20260515-0939 | read | 30b89f5bdb500dadd509c221746de8652b669b3a10f6ffc2f95888dfefc8edd6 |
| 20260515-0941 | read | 388cf5fbaad7c15deb6234db5979e206f0d2ba8dfe880075ead28905e91cb215 |
| 20260515-0946 | read | 7ee8995376d017a55c31732ca61a94bbb64b73dfe12bb1343f37ab95117db53c |
| 20260515-0950 | read | 3f6a95edf1df3494239715096477fcf60e1a5cd7c90a20990651172fa470f795 |
| 20260515-0951 | read | 161b8c022888ac4aee0e06e0986a2f383b6a64d19a91e068104cb8feb9718e4e |
| 20260515-0952 | read | 46f585a6eaf5b5eb4cc130aeb71507987c215f491a65d56579cd9fcf74ab31b9 |
| 20260515-0956 | read | b483e57d53d0189a4050eee8b7f39f1b3df6697c736ec634fbd4b9a4efdd6ce7 |
| 20260515-0957 | read | f7b621b0eee5db06a7a3dd64a7a75b8d009688a797db7b05abf98cf21caa9f14 |

## Limits

- Archive gaps remain unfilled; a sampled zero is not evidence that the lane stayed empty between readings.
- A repeated feed lane count does not prove that a SUMO edge is mapped to the right physical carriageway.
- No detector mapping, OSM tag, geometry, lane count, or traffic observation is changed.

## Raw lane readings

Volumes are the feed's raw values for each observed period. Missing archive periods are not filled.

| Detector | Period start | Lane | Raw volume | Valid | Period seconds |
|---|---|---|---:|---|---:|
| AID01104 | 2026-05-15T08:35:00+08:00 | Fast Lane | 8.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:35:00+08:00 | Slow Lane | 1.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:35:30+08:00 | Fast Lane | 5.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:35:30+08:00 | Slow Lane | 2.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:38:00+08:00 | Fast Lane | 3.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:38:00+08:00 | Slow Lane | 5.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:38:30+08:00 | Fast Lane | 9.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:38:30+08:00 | Slow Lane | 2.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:40:00+08:00 | Fast Lane | 7.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:40:00+08:00 | Slow Lane | 2.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:40:30+08:00 | Fast Lane | 9.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:40:30+08:00 | Slow Lane | 3.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:42:00+08:00 | Fast Lane | 11.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:42:00+08:00 | Slow Lane | 3.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:42:30+08:00 | Fast Lane | 9.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:42:30+08:00 | Slow Lane | 2.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:43:00+08:00 | Fast Lane | 3.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:43:00+08:00 | Slow Lane | 5.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:43:30+08:00 | Fast Lane | 5.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:43:30+08:00 | Slow Lane | 4.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:44:00+08:00 | Fast Lane | 10.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:44:00+08:00 | Slow Lane | 6.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:44:30+08:00 | Fast Lane | 3.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:44:30+08:00 | Slow Lane | 3.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:45:00+08:00 | Fast Lane | 8.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:45:00+08:00 | Slow Lane | 1.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:45:30+08:00 | Fast Lane | 4.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:45:30+08:00 | Slow Lane | 1.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:46:00+08:00 | Fast Lane | 4.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:46:00+08:00 | Slow Lane | 2.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:46:30+08:00 | Fast Lane | 7.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:46:30+08:00 | Slow Lane | 1.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:49:00+08:00 | Fast Lane | 8.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:49:00+08:00 | Slow Lane | 4.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:49:30+08:00 | Fast Lane | 6.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:49:30+08:00 | Slow Lane | 3.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:50:00+08:00 | Fast Lane | 3.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:50:00+08:00 | Slow Lane | 1.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:50:30+08:00 | Fast Lane | 8.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:50:30+08:00 | Slow Lane | 2.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:54:00+08:00 | Fast Lane | 2.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:54:00+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:54:30+08:00 | Fast Lane | 1.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:54:30+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:56:00+08:00 | Fast Lane | 5.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:56:00+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:56:30+08:00 | Fast Lane | 4.0 | True | 30.0 |
| AID01104 | 2026-05-15T08:56:30+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:00:00+08:00 | Fast Lane | 7.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:00:00+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:00:30+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:00:30+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:05:00+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:05:00+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:05:30+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:05:30+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:09:00+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:09:00+08:00 | Slow Lane | 2.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:09:30+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:09:30+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:12:00+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:12:00+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:12:30+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:12:30+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:14:00+08:00 | Fast Lane | 2.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:14:00+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:14:30+08:00 | Fast Lane | 2.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:14:30+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:18:00+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:18:00+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:18:30+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:18:30+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:19:00+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:19:00+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:19:30+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:19:30+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:20:00+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:20:00+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:20:30+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:20:30+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:23:00+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:23:00+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:23:30+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:23:30+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:25:00+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:25:00+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:25:30+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:25:30+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:28:00+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:28:00+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:28:30+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:28:30+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:30:00+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:30:00+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:30:30+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:30:30+08:00 | Slow Lane | 1.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:32:00+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:32:00+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:32:30+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:32:30+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:35:00+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:35:00+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:35:30+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:35:30+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:40:00+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:40:00+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:40:30+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:40:30+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:43:00+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:43:00+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:43:30+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:43:30+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:44:00+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:44:00+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:44:30+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:44:30+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:45:00+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:45:00+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:45:30+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:45:30+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:49:00+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:49:00+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:49:30+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:49:30+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:50:00+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:50:00+08:00 | Slow Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:50:30+08:00 | Fast Lane | 0.0 | True | 30.0 |
| AID01104 | 2026-05-15T09:50:30+08:00 | Slow Lane | 0.0 | True | 30.0 |
