# DirectPilot — Mobile frontend UX audit and navigation stabilization (2026-10-15)

## Mandatory scope and boundaries
- **Canonical acceptance URL:** `https://uat.directpilot.ir`, GitHub `namach2727-coder/directpilot-web`, branch `UAT`, Vercel project `directpilot-web`.
- **Production `directpilot.ir` remains independent** on GitHub `main`. No Production alias, Render backend/database, production Neon, real Meta webhook, or payment data change is authorized by this work.
- UAT backend remains Vercel `directpilot-uat-api` + independent Neon UAT DB `neondb`, Alembic `0027_traceable_receipt_versions`. Receipt evidence/images remain PostgreSQL BYTEA; no R2/S3. All receipt versions remain traceable by customer for 4+ months subject to recoverable backup acceptance.

## Findings and changes implemented in UAT
- Before: public full-screen mobile navigation had an `×` close affordance but no explicit **بازگشت** label; browser-back/route changes and scroll could leave an unclear return path. After: explicit always-visible fixed Back button, Escape dismissal, focus cycle/focus restoration, page-scroll restoration and route-path-aware dismissal, with 48px touch controls and iPhone safe-area accommodation.
- Before: authenticated customer/admin mobile navigation used plain `<details>` with only a menu summary and no independent Close or Back-to-overview action; behavior for outside tap, Escape, browser history and narrow display was incomplete. After: one shared customer/admin mobile menu with labeled toggle, accessible expanded state and controls, distinct Close button, back-to-overview/back-to-site link, current section label, click-outside/Escape/history/resize dismissal, >44px targets, scrollable menu and mobile safe-area layout.
- Before: login/register/checkout/payment result routes depended on individual links or Logo; some initial/error states had no consistently visible Back route. After: common `Frame` has deterministic Back to site or account billing; backend/payment actions unchanged.
- Before: long Automation Rules editor placed Cancel below a long mobile form. After: fixed-in-scroll sticky top Back control (disabled while saving) with existing bottom Cancel retained; no draft mutation initiated by navigation alone.
- Before: error boundary only offered Retry. After: a separate home Return link.
- Site/UI remains Persian RTL, preserves role gating and same-origin auth session routing.

## Git, tests and deployment evidence
- GitHub PR `namach2727-coder/directpilot-web#32` merged into branch `UAT` at **`dad3a3790246f96fbbe760d26e2415afd0a45851`**.
- Backup branch BEFORE the merge: **`backup/uat-before-mobile-navigation-20261015`** at UAT source SHA `08828ee1358ead2e9d81d2985fe2e4b07020e355`.
- PR final feature commit `176dbeb712e780aa1ce0b8630745da18f4025039` passed GitHub Actions **223/223 tests**, TypeScript, ESLint and Next.js build; no test failures.
- Official Vercel UAT deployment `dpl_GGgg4EkaQF3bExfnzbfgRBK1GLhj` from UAT SHA `dad3a379...` READY. Alias `uat.directpilot.ir` confirmed on that deployment; commercial Production `directpilot.ir` alias remained `dpl_cRZsk7rndqFWH1KnKdhLVbNU1VxF`.
- Official UAT Domain Smoke GitHub Actions run `38709714205` PASS and Official UAT HTTP Diagnostic run `38709713924` PASS. Both check protected HTTP/routing, not mobile browser layout. UAT Customer Journey Quality post-merge run `38709714016` was still in progress at initial checkpoint; confirm current result before claiming whole merge CI PASS.
- Source-reviewed routes: public marketing/menu/login/register, customer dashboard navigation + billing/payment/receipt states, admin dashboard/payments/history, long automation modal, error and not-found pages. This is a **code and CI review**, not a complete visual/device-lab audit.

## Remaining physical-device acceptance — DO NOT report PASS yet
With an authorized Vercel SSO reviewer, test canonical `https://uat.directpilot.ir` on iPhone Safari (390px / 375px) and Android Chrome (360px), plus narrow 320px, 768px tablet and desktop:
1. Public navigation open → Back visible while scrolling, Escape on hardware keyboard, tap Login/register link, browser hardware/gesture Back; body scroll restored; no menu retained after route changes.
2. Customer login → Dashboard → Automation / Instagram / Business / AI / Billing / Security; menu opens, close button, tap outside, back to overview and footer navigation. Refresh session and logout do not regress.
3. Admin login → Overview / Products / Customers / Subscriptions / Payments / Audit / Security; menu close/back, role isolation, long labels and no viewport overflow.
4. Checkout → card transfer → receipt upload form; Back always works without submitting duplicate payments or losing confirmed payment state. Use dummy UAT data only; no real transfer approvals.
5. Automation editor with long scroll: header Back remains reachable; saving disables exit; Cancel/Back must not accidentally submit.
6. Accessibility: RTL, VoiceOver/TalkBack naming, tab focus, Escape, button 44px minimum, virtual keyboard/input focus, iOS safe areas, horizontal overflow, scroll containment and responsive touch. Check reduced-motion settings.
7. Functional archive (separate): historical receipt version display/search, associated customer privacy and PostgreSQL durability after redeploy.
8. If a page redirects to `vercel.com/sso-api`, complete authorized Vercel SSO. **Never disable protection just to pass unauthenticated checks.**

## Further redesign opportunities (not approved as completed)
- Usability discovery with actual mobile screenshots and user sessions for dense customer billing, admin payment filter/detail layouts, onboarding and lengthy Knowledge/Automation forms.
- Consider sticky bottom navigation or task-centric IA only after confirming the critical top tasks and role-based information architecture; do not silently remove module-specific paths.
- Conduct real-device performance profiling (cold auth/me timings, TTI, scroll/jank), accessibility audit and cross-browser visual regression before declaring mobile UX fully accepted.
- Retain all five canonical docs in order `AI_HANDOFF.md` → `PROJECT_ROADMAP.md` → `DECISIONS.md` → `CURRENT_STATE.md` → `NEXT_ACTIONS.md`. Owner need not repeat mobile Back requirements in future chats.

## Production hard stop
Production migration remains an independent blocked project requiring UAT business acceptance, commercial hosting compliance, recoverable source backup, final fresh DB transfer with data parity, webhook writer freeze/replay, rollback drill and explicit owner GO. Do not treat these mobile fixes as Production go-live signoff.
