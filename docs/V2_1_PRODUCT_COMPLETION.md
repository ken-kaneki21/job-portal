
# V2.1 Product Completion

This batch closes the remaining local product UX gaps before deployment.

## Included

- Portal import UI for LinkedIn, Naukri, Foundit and Indeed CSV/JSON exports.
- Backend upload endpoint using the existing normalization, dedupe and provenance pipeline.
- Hiring-post intelligence endpoint and UI for user-visible post text.
- Live Applications board backed by `/applications` instead of placeholder cards.
- Existing review-first Workday/application-assist safety retained.
- No blind final submission.
- No credential scraping.
- Deterministic extraction tests for hiring-post intelligence.

## Deployment boundary

Cloud deployment, authentication, production secrets, TLS/domain configuration and
production smoke verification remain deployment work because they require external
infrastructure/account choices.
