# 01-NUTRITION

Version: 1.0.0

Canonical location: Existing fitness workbook: legacy ДНЕВНИК plus FOOD_LOG new raw additions; FOOD_REFERENCE aliases ПРОДУКТЫ; DAILY_SUMMARY recomputed from current raw rows. Never sum component foods and overlapping meal/day totals.

Protocol: Read requested date(s), FOOD_LOG additions, conflicts, and relevant source references. Missing calories imply PARTIAL; an incomplete day is not zero. Corrections are new rows with supersedes. Never trust ИТОГИ as complete without reconciling raw diary: it may omit newer days.

Current state: retrieve the domain-filtered shared DOMAIN_STATE and the exact native dataset in STORAGE-MAP. Shared logs expose domain-filtered CHANGELOG (OPERATIONS), SOURCE (PROVENANCE) and INCIDENTS, rather than twelve duplicate log files. Empty/inactive domains remain registered routes with no invented records.
