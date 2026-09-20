# SQL migration validation

Validated on September 20, 2026 using an isolated PGlite 0.5.8 PostgreSQL engine.
No connection to the user's PostgreSQL server was made.

The test imported the Florida rows from the official CMS August 13, 2026 release
(previously downloaded September 19). All raw columns were text. The production
views include an explicit Florida filter and also accept full national CSVs.

| Cleaned result | Rows |
| --- | ---: |
| Florida hospitals | 221 |
| South Florida hospitals including Palm Beach | 53 |
| Hospital survey measure records | 12,988 |
| Florida benchmark records | 51 |

Checks passed:

- Raw schema creation and SQL cleaning executed successfully.
- Cleaning ran twice against unchanged raw data successfully.
- Every analysis query and quality-check query executed.
- Duplicate-key checks returned no rows for the source extract.
- All survey facility IDs matched hospital records.
- All three selected measures had matching state reporting periods.
- Invalid dates became NULL; a valid leap-day date parsed correctly.
- Suppressed and out-of-range percentages became NULL; a true zero remained zero.
- A deliberately repeated hospital import caused the duplicate guard to reject cleaning.

Views retain unavailable ratings and original footnotes. No Tableau workbook was
created or validated as part of this change. DataGrip import and the user's
PostgreSQL connection still need to be configured locally following the README.
