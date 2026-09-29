# Build pipeline

The published HTML is committed and served as is (GitHub Pages, `main`, root).
Since September 2026 everything that shows a rating is generated from one data
layer. Do not edit ratings, titles or descriptions in the HTML by hand.

## Data

| File | Role |
|---|---|
| `data/Beständigkeitsliste Bürkle.xlsx` | The source. Never edited. |
| `resistance_data.py` | Reads the spreadsheet: concentration, estimates `( )`, pitting `L`, `K`, synonym rows. |
| `diagrams.py` | Inline SVG diagrams. Rules are in its docstring: no script, hex colours, 320-wide viewBox, title and desc. |
| `data/chemical_names_en.json` | English name for each German source name. |
| `data/chemical_pages.json` | Which chemicals have a page, the source row group each page shows, names in six languages, redirects. |
| `data/chemical_classes.json` | Chemical class of each chemical, assigned by hand. Read through `class_stats.py`. |
| `data/rating_overrides.json` | Corrected and disputed values, each with a reason and references. |
| `data/chemicals_burkle_full.json` | OUTPUT for the in-browser tools. Written by `export_frontend_data.py`. |

## Build, in this order

```bash
python3 resistance_data.py          # summary only, checks that overrides apply
python3 export_frontend_data.py     # data for homepage lookup, compare, charts
python3 build_chemical_pages.py     # chemical pages, pair pages, chemicals index, About corrections list
python3 build_material_tables.py    # tables inside the material pages
python3 build_chart_tables.py       # static rows and group figures in chart pages
python3 build_compare_pages.py      # comparison pages (en, de, es) and the compare index
python3 fix_page_quality.py         # badge colours and structured data on patched pages
python3 fix_internal_links.py       # run twice if it reports changes
python3 noindex_french.py           # keeps French out of the index, see below
python3 build_sitemap.py            # always last
```

Every script takes `--check` and is idempotent. `fix_cross_language.py`,
`fix_consent_order.py` and `patch_generators.py` still apply; run the `build_*`
scripts again after `fix_cross_language.py`.

## Index policy

| Pages | Robots | Sitemap |
|---|---|---|
| Chemical pages en, de, es (193 each) | indexable | yes |
| Material pages en, de, es | indexable | yes |
| Charts, compare, tools en, de, es | indexable | yes |
| Pair pages en, de, es with a rating | `googlebot: noindex,follow` | no |
| Pair pages without a rating | `robots: noindex,follow` | no |
| Everything fr, pt, zh | `robots: noindex,follow`, no hreflang pointing at it | no |
| Redirect stubs | `robots: noindex,follow`, no ad or analytics tags | no |

French was taken out of the index on 2026-09-28 (`noindex_french.py`), so only
English, German and Spanish are indexed.

The pair-page policy is one constant, `PAIR_ROBOTS` in `build_chemical_pages.py`.

## Adding a chemical page

Add an entry to `data/chemical_pages.json` with the exact German name of the
source row group as `source`, and the six names. Run the build. A page never
picks its data by name matching.

## Changing a rating

Add an entry to `data/rating_overrides.json`. Use `corrected` only when at
least two independent published sources disagree with the source in the unsafe
direction; otherwise `disputed`. Give the references.

## Retired scripts

`generate_chemical_pages.py`, `generate_chemical_material_pages.py`,
`generate_pair_pages.py`, `enrich_chemical_pages.py`, `create_chemicals.py`,
the `add_*.py`, `fix_ratings*.py`, `fix_*mappings.py`, `ctr_optimize*.py`,
`fix_meta_descriptions.py`, `seo_*.py`, `generate_zh_pages.py`,
`rebuild_materials.py`, `fix_german_chemical_names.py` and `build_index.py`
exit with a message. They are kept for history only.
