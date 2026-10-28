# Security policy
Report vulnerabilities privately via GitHub Security Advisories (Security tab > Report a vulnerability). Do not open public issues for security bugs.

## Controls in this repo
- Server-side API keys (env vars only); `.env` is git-ignored.
- Strict CSP and no-referrer on the static site; security headers on the API.
- Prompt-injection filter, email/phone redaction, input caps, per-IP rate limits.
- Optional API key (`APP_API_KEY`) and MCP token (`MCP_TOKEN`); MCP is off by default.
- Fernet-encrypted vault and SHA-256 hash-chained audit log (`/api/audit/verify`).
- Containers: non-root user, read-only filesystem, no-new-privileges; k8s pods run non-root with seccomp.

## Known limits
Browser-side keys are visible to the person using the browser. ZK proofs, Wasm sandboxing, JWT/RBAC and a full post-quantum handshake are not implemented yet.
