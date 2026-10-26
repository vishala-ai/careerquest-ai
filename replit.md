# CareerQuest AI — authenticated Replit handoff

Read AGENTS.md and docs/CLOUD_DEPLOYMENT.md first. Import the existing app; do not rebuild it. This is an alias-only external demo for Grades 9–12, not a production system for real student information.

Run builds dependencies and starts FastAPI serving React on port 8000. Self-registration and username/password login are required. Each account owns one Explorer; server-side sessions and ownership gates protect all profile, research, history and PDF endpoints. Do not restore the old browser-local selector as an authorization mechanism. Existing local profiles are deliberately not in this package and must never be publicly claimable.

For publishing, use scripts/replit-production.sh, managed persistent PostgreSQL DATABASE_URL, and the exact HTTPS CAREERQUEST_PUBLIC_ORIGIN. The launcher disables developer tools and refuses ephemeral SQLite. Preview can derive its HTTPS origin from Replit’s server-provided REPLIT_DEV_DOMAIN. See docs/CLOUD_DEPLOYMENT.md for production configuration, host-only account assignment/reset and verification.

Preserve Groq (openai/gpt-oss-120b), LangGraph, source validation, XP, profile confirmation, versioned histories, the emerald milestone and graphical portfolio. Local SQLite and Streamlit fallback remain available; do not expose Streamlit publicly. GROQ_API_KEY belongs only in server-side Secrets; never display it, inspect its value or put it in React. No model provider change is requested. Retrieval is curated offline content, not live verified research.

The source ZIP excludes .env, databases, installed dependencies and screenshots. It does not migrate, delete or reset local records. Do not include credentials or working databases in an import archive. Read the deployment doc before publishing and verify storage after a real restart/redeploy.
