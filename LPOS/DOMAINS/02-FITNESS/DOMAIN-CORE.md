# 02-FITNESS

Version: 1.0.1
Updated: 2026-10-02T17:00:56.808Z
Reason: deployed source-derived activity/body/goal views in the existing fitness workbook.

Canonical raw sources are dated ДНЕВНИК activity leaves and ПРОФИЛЬ И ЦЕЛИ observations/goals. ACTIVITY_LOG, BODY_METRICS and GOALS are read-only typed projections with source provenance. Read live DATASETS to resolve authority. Compare source hashes before use; never create a competing exercise log.

Completed activity differs from plans in ТРЕНИРОВКИ. Estimated energy differs from measured quantity. Activity aggregates and their leaf rows overlap. Do not add steps within a workout twice, or wearable Total Calories to BMR. Estimated expenditure in DAILY_SUMMARY is only the legacy reported active-energy aggregate; total expenditure/deficit stays null unless independently justified. Keep overlap/method uncertainty.

Body measurements are dated USER_REPORTED observations with conditions, not today's weight. Unknown historical dates remain unknown; retain narrative history at its source. Goals require temporal context and current confirmation when old. Append raw corrections with supersedes and audit; refresh typed views; never delete earlier observations. Domain-filtered shared Control logs provide current state, source, changes and incidents.
