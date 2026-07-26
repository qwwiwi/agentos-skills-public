# Build vs Buy Decision Matrix

Use this matrix when evaluating EdTech components. Score each criterion 1-5.

| Component | Build score factors | Buy score factors |
|-----------|-------------------|------------------|
| Video hosting | Custom DRM needs, unique UX | Standard delivery, cost-sensitive |
| Payment/billing | Custom pricing models, multi-currency | Standard plans, fast launch |
| Auth/identity | Unique auth flows, compliance needs | Standard OAuth, fast launch |
| Email/notifications | Custom triggers, high volume | Standard transactional, low volume |
| LMS core | Unique pedagogy, IP differentiation | Standard course delivery |
| Analytics | Custom metrics, AI-driven insights | Standard dashboards |
| Real-time collab | Core product feature | Nice-to-have feature |
| AI/LLM features | Core differentiator | Supplementary feature |

### Decision Rules

- **Build** when: core differentiator, unique IP, full control needed, team has expertise
- **Buy** when: commodity feature, time-to-market critical, no in-house expertise, proven SaaS
- **Wrap** (build adapter around bought): need customization but not from scratch

### Common EdTech Buy Options

| Component | SaaS Options | Self-hosted Options |
|-----------|-------------|-------------------|
| Video | Mux, Cloudflare Stream, Bunny Stream | MediaCMS, PeerTube |
| Payments | Stripe, LemonSqueezy, Paddle | -- |
| Auth | Supabase Auth, Clerk, Auth0 | Keycloak, Authentik |
| Email | Resend, Postmark, SendGrid | Postal |
| Search | Algolia, Typesense Cloud | Meilisearch, Typesense |
| Analytics | PostHog, Mixpanel | Plausible, Umami |
