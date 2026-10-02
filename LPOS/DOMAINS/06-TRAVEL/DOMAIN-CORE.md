# 06-TRAVEL

Version: 1.0.0

Canonical location: Shared DOMAIN_STATE for trips and dated booking status; source booking documents in Drive/Library.

Protocol: Plan, reservation, paid, checked-in, cancelled and completed are different statuses. Do not infer present location from an old hotel booking.

Current state: retrieve the domain-filtered shared DOMAIN_STATE and the exact native dataset in STORAGE-MAP. Shared logs expose domain-filtered CHANGELOG (OPERATIONS), SOURCE (PROVENANCE) and INCIDENTS, rather than twelve duplicate log files. Empty/inactive domains remain registered routes with no invented records.
