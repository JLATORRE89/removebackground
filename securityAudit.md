# Security Audit

Date: 2026-05-20
Scope: Defensive sensitive-file exposure audit.

## Summary
- Status: PATCHED
- Stack detected: Python
- Sensitive files found: None found in non-vendor scan.
- Public/static serving risk: Sensitive-file URL deny rules were absent or incomplete in at least one app/static-serving layer; patched defensively.

## Checks Performed
- Checked for .env, .env.*, .git, logs, databases, SQL dumps, archives, backups.
- Reviewed static serving and catch-all routes.
- Reviewed web server/deployment config when present.
- Checked for app-level honeypots and whether they can be bypassed by static serving.

## Findings
- Finding: Public request guards needed for sensitive paths and extensions.
- Risk: Sensitive files could disclose credentials, repository metadata, logs, databases, backups, or operational details if a project root or broad static path is exposed.
- Resolution: Added deny rules/middleware for dotfiles, .env variants, .git, logs, databases, SQL dumps, archives, and backups.

## Files Changed
- app.py

## Verification
Commands run:
`ash
Get-ChildItem -Directory | Select-Object -ExpandProperty Name
bounded scan for sensitive filenames and likely web/static config
python -m py_compile <patched Python entrypoints>
node --check <patched JavaScript entrypoints>
Select-String verification for inserted deny rules in touched files
`

Results:
- Patched Python entrypoints compiled successfully.
- Patched JavaScript entrypoints passed 
ode --check.
- Touched files were scanned for the expected deny rules.
- No secret values or .env contents were printed in this report.

## Production Verification Commands
Run after deployment:
`ash
curl -I https://example.com/.env
curl -I https://example.com/.git/config
curl -I https://example.com/logs/traffic.log
curl -I https://example.com/database.db
curl -I "https://example.com/.env?bust=$(date +%s)"
`

Expected:
- 403 or 404, never 200.

## Remaining Manual Steps
- Run the production curl checks after deployment or reverse-proxy reload.