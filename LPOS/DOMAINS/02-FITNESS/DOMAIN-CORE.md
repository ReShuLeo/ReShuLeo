# 02-FITNESS

Version: 1.0.0

Canonical location: ACTIVITY_LOG extensions plus legacy activity sections; BODY_METRICS time series; GOALS aliases the existing profile/goal tab.

Protocol: Separate planned workouts from completed logs. Do not add steps within workouts twice, or wearable Total Calories to BMR. Report measurement conditions and the latest observation date.

Current state: retrieve the domain-filtered shared DOMAIN_STATE and the exact native dataset in STORAGE-MAP. Shared logs expose domain-filtered CHANGELOG (OPERATIONS), SOURCE (PROVENANCE) and INCIDENTS, rather than twelve duplicate log files. Empty/inactive domains remain registered routes with no invented records.
