# Security Threat Model

## Protected assets

- resident addresses and contact information;
- volunteer profiles and schedules;
- collection history;
- recycler receipts and verified weights;
- governance identities;
- API credentials and production secrets;
- audit events and backups.

## Principal threats and controls

| Threat | Initial controls | Required before broad launch |
|---|---|---|
| Account takeover | strong password validation, JWT expiry, password-change flow | MFA/passkeys, login alerting |
| Broken object authorization | role and ownership filtering in API querysets | independent authorization test review |
| Malicious upload | authenticated upload fields | object storage, MIME validation, malware scanning |
| Address leakage | no public request endpoint; aggregate public metrics | field-level access audit and privacy testing |
| Administrator abuse | reserved roles and audit events | external append-only log destination and dual approval |
| Spam requests | authenticated submission | email verification, rate limits, abuse controls |
| Database loss | persistent volume | encrypted daily off-site backups and restore drills |
| Secret disclosure | `.env` excluded from Git | secret manager, rotation and repository scanning |
| Dependency compromise | pinned compatible versions and CI | Dependabot and release review |

## Explicit non-goal

EcoRevive OS does not include covert accounts, hidden backdoors or unaudited administrator impersonation.
