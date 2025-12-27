# Dialect Catalog

This project maintains a dialect catalog to normalize Malaysian Malay variants for retrieval
while keeping user phrasing intact for generation. Dialects are tracked in a single source of
truth and explicitly marked as `active` or `draft` to keep production behavior stable.

Where to add or update
- `src/data/shortforms.json`: add a dialect entry under `dialects` with `_description`,
  `_status`, and any lexicon terms.
- `src/summarization/preprocessing.py`: update `DialectDetector.DIALECT_INDICATORS` and
  `DialectDetector.DIALECT_NAMES` for new dialect codes.
- `src/validation/benchmark.py`: add dialect examples to `DIALECT_TESTS` when activating.

Status semantics
- `active`: included in normalization and dialect detection.
- `draft`: cataloged only; ignored by normalization and dialect detection.
- Optional `_min_matches`: minimum indicator hits needed before detection fires (defaults to 1).

Quality checks
- `scripts/validate_shortforms.py` enforces required metadata.
- `reports/lexicon_report.md` summarizes coverage and overlaps.

Activation checklist
1. Add vetted lexicon terms to `src/data/shortforms.json`.
2. Add indicator tokens to `DialectDetector.DIALECT_INDICATORS`.
3. Add display name to `DialectDetector.DIALECT_NAMES`.
4. Add detection tests in `DIALECT_TESTS`.
5. Flip `_status` to `active` and run `./scripts/run_deep_tests.sh`.

Current dialect catalog
| Code | Status | Description |
| --- | --- | --- |
| kelantanese | active | Kelantan dialect - characterized by unique vowel sounds and distinct vocabulary |
| terengganu | active | Terengganu dialect - similar to Kelantanese with unique variations |
| kedah_perlis | active | Kedah and Perlis dialect - Northern Malay |
| perak | active | Perak dialect - distinctive vocabulary |
| negeri_sembilan | active | Negeri Sembilan dialect - influenced by Minangkabau |
| penang | active | Penang dialect - heavily influenced by Hokkien |
| sabah | active | Sabah dialect - East Malaysian with distinct vocabulary |
| sarawak | active | Sarawak dialect - distinctive East Malaysian vocabulary |
| johor_riau | draft | Johor-Riau Malay (Southern Malay; basis for Standard Malay) |
| melaka | draft | Melaka Malay (southern coastal Malay with Peranakan influence) |
| pahang | draft | Pahang Malay (East Coast Malay with distinct vowel shifts) |
| selangor_kl | draft | Selangor/Klang Valley Malay (urban Central Malay with modern colloquialisms) |
| kedah | draft | Kedah Malay (Northern Malay, split from Kedah/Perlis for finer granularity) |
| perlis | draft | Perlis Malay (Northern Malay closely related to Kedah) |
| labuan | draft | Labuan Malay (Borneo coastal Malay influenced by Brunei/Sabah) |
| brunei_malay | active | Brunei Malay (Borneo Malay used in Brunei, Sabah, and Labuan) |
| banjar | active | Banjar Malay (Banjarese community in Sabah/Johor; Malayic variety) |
| minangkabau | active | Minangkabau (Malayic variety; Negeri Sembilan heritage influence) |
| baba_malay | active | Baba Malay (Peranakan/Straits Chinese Malay creole) |
| chitty_malay | draft | Chitty Malay (Peranakan Indian Malay creole) |
| bazaar_malay | active | Bazaar/Pasar Malay (contact Malay used in trade settings) |
| patani_malay | draft | Patani/Thai-Malay (Kelantanese-related variety in Southern Thailand) |

Notes
- Newly activated dialects use a seed lexicon and require native-speaker validation before expanding coverage.
