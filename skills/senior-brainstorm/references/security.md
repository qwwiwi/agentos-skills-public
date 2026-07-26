---
last_verified: 2026-04-15
applies_to: [early-stage, growth, scale]
confidence: high
---

# Security

## Threat Modeling (первый шаг)

Перед выбором инструментов -- модель угроз:

| Компонент | Actors | Assets | Threats |
|-----------|--------|--------|---------|
| Auth | Злоумышленник, бывший сотрудник | Учетные записи, сессии | Credential stuffing, session hijacking |
| Payments | Злоумышленник, мошенник | Платежные данные, подписки | Fraud, webhook spoofing |
| Content | Студент, инструктор | Видео, курсы, IP | Пиратство, несанкционированный доступ |
| Data | Внешний атакующий, insider | PII, аналитика | SQL injection, data exfiltration |
| API | Bot, scraper | Endpoints, rate limits | DDoS, enumeration, abuse |

## Application Security

- **Helmet** -- security headers (CSP, HSTS, X-Frame-Options)
- **Zod** -- runtime validation на каждом boundary (API input, forms, webhooks)
- **Prisma/Drizzle** -- parameterized queries (SQL injection prevention)
- **CSP headers** -- снижает риск XSS (не решает полностью)
- **@edge-csrf/nextjs** -- CSRF tokens для App Router
- **rate-limiter-flexible** -- brute-force protection на auth endpoints
- **Cloudflare WAF** -- managed rules, zero-day protection

**Anti-pattern:** CSP != "решение XSS". Основа: escaping, sanitization, отказ от dangerouslySetInnerHTML.

## Secure File Upload Pipeline

1. MIME type validation (не доверять расширению)
2. File size limits
3. Antivirus scanning (ClamAV)
4. Signed upload URLs (S3 presigned / Supabase Storage)
5. Quota enforcement per user/tenant
6. Sanitization (strip EXIF, re-encode images)

## Auth Hardening

- JWT: access token 5-15 мин, refresh token 7-30 дней (зависит от threat model)
- Refresh token rotation: single-use, hash в DB
- MFA: `otplib` (TOTP, RFC 6238) + backup codes
- Session revocation: Redis-backed, device/session visibility
- Step-up auth для sensitive operations (change password, payment)
- Rate limiting на login: 5 attempts, exponential backoff

## Secrets Management

| Стадия | Инструмент | Почему |
|--------|------------|--------|
| Early-stage | .env + SOPS (encrypted in Git) | Просто, version controlled |
| Growth | Infisical / Doppler | UI, rotation, audit log |
| Enterprise | HashiCorp Vault + ESO | Dynamic credentials, KMS, HSM |

- **Gitleaks** -- pre-commit hook для утечек секретов
- Rotation policy: 90 дней для API keys, instant при утечке

## Encryption

- **In transit**: TLS 1.3 (enforced), mTLS между сервисами
- **At rest**: managed disk encryption (AWS EBS, GCP) -- default
- Column-level encryption для PII: `pgcrypto` или application-level AES
- Backup encryption: обязательно

## Security Testing Pipeline

| Этап | Инструменты | Timing |
|------|-------------|--------|
| Pre-commit | Gitleaks (секреты), ESLint security plugin | Local, instant |
| PR gate | Semgrep (SAST), npm audit | < 90 сек |
| Merge | Trivy + Grype (SCA), Syft (SBOM), Cosign (подпись) | Async |
| Pre-deploy | Kyverno (reject unsigned images) | Blocking |
| Nightly | OWASP ZAP (DAST) | Async |

## Supply Chain Security

- Lockfiles committed (`package-lock.json` / `pnpm-lock.yaml`)
- Dependency pinning (exact versions)
- SBOM generation: Syft (CycloneDX)
- Artifact signing: Cosign (Sigstore)
- Base image policy: distroless / slim, pinned SHA
- Dependabot / Renovate для автоматических PR обновлений
- npm audit: `--audit-level=high` в CI

## Compliance

| Стандарт | Когда | Действия |
|----------|-------|----------|
| GDPR | Пользователи из EU | Privacy by design, DPA, права пользователей (export/delete) |
| SOC 2 | B2B клиенты | Автоматизация через Vanta/Drata |
| PCI DSS | Платежи | Offload на Stripe (SAQ A) |

## Audit Logging

- Immutable audit trail: кто, что, когда, откуда
- Tamper-evidence (append-only, signed entries)
- Retention: 1 год минимум (compliance)

## Incident Response

1. Detect (мониторинг, алерты)
2. Triage (severity, scope, blast radius)
3. Contain (isolate, disable, block)
4. Fix (patch, rotate credentials)
5. Post-mortem (blameless, action items)
6. Disclosure (если PII затронуты)
