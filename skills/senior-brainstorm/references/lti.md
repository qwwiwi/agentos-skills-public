# LTI (Learning Tools Interoperability)

### Overview

LTI enables integration with LMS platforms (Canvas, Moodle, Blackboard, Google Classroom).
Critical for B2B EdTech selling to schools/universities.

### Versions

| Version | Features | When to use |
|---------|----------|------------|
| LTI 1.1 | Basic launch, grade passback | Legacy LMS support only |
| LTI 1.3 Core | OAuth 2.0 + JWT launch (authentication and context only) | New integrations (minimum viable) |
| LTI Advantage | 1.3 Core + service layers: Deep Linking, AGS (Assignment and Grade Services), NRPS (Names and Role Provisioning Service) | Full LMS integration (grades, rosters, content selection) |

**Important distinction:** LTI 1.3 Core provides only the secure launch mechanism
(OAuth 2.0 + JWT). Deep Linking, AGS, and NRPS are separate service specifications
layered on top as part of LTI Advantage. Scoping work as "LTI 1.3" without specifying
which Advantage services are needed will underestimate implementation effort.

### Implementation Checklist

- [ ] Platform registration (issuer, client_id, deployment_id)
- [ ] JWKS endpoint for key management
- [ ] OIDC login initiation endpoint
- [ ] Launch endpoint with JWT validation
- [ ] Grade passback via Assignment and Grade Services (AGS)
- [ ] Roster sync via Names and Role Provisioning Services (NRPS)
- [ ] Deep linking for content selection

### Architecture Notes

- LTI 1.3 uses OAuth 2.0 + JWT -- fits API-first design naturally
- Store platform registrations in DB (multi-tenant ready)
- Grade passback is async -- use job queue (BullMQ, Celery)
- Test with 1EdTech (formerly IMS Global) reference implementation before real LMS

### OneRoster / SIS Sync

OneRoster (1EdTech standard) defines a REST API and CSV format for syncing student
rosters, classes, enrollments, and demographics between Student Information Systems (SIS)
and learning tools. Critical for B2B sales to schools and districts -- many procurement
processes require OneRoster support.

| Aspect | Detail |
|--------|--------|
| Protocol | REST API (v1.1, v1.2) or CSV bulk import |
| Data | Users, orgs, classes, enrollments, demographics |
| When needed | Selling to K-12 districts, university admin integration |
| Relation to LTI | Complementary -- LTI handles launch, OneRoster handles provisioning |

### SCORM / xAPI / cmi5 (Content Packaging Standards)

| Standard | Purpose | When to use |
|----------|---------|------------|
| SCORM 1.2/2004 | Legacy content packaging + tracking (completion, score) | Importing existing courseware from other LMS |
| xAPI (Experience API) | Flexible learning activity statements ("actor-verb-object") | Rich analytics, mobile/offline learning, cross-platform tracking |
| cmi5 | xAPI profile for LMS launch + tracking (bridges SCORM and xAPI) | New content packages that need xAPI flexibility with LMS launch conventions |

**Guidance:** If importing legacy content, SCORM support is table-stakes. For new content
and advanced analytics, xAPI provides richer data. cmi5 is the recommended bridge when
you need both LMS launch conventions and xAPI flexibility. All three are 1EdTech
(formerly IMS Global) standards.
