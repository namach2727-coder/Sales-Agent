# DirectPilot GSC daily breakpoint verification — 2026-10-18

## Scope and evidence
READ-ONLY SEO investigation, performed after reading all six mandatory DirectPilot continuity artifacts. No Production deployment, UAT deployment, indexing flag, Google property, database, payment or Meta/Telegram configuration was modified. Owner authorization: request to read six files and continue current project; findings documented only in draft documentation branch pending review.

- Source: Connected Windsor.ai `searchconsole` account `sc-domain:directpilot.ir`, Search Analytics **Web Search**.
- Direct query: `date, impressions, clicks, position`, 2026-08-21 through 2026-10-15, 56 daily source rows (2026-10-16 onward excluded due to data settling).
- Page verification: dimension `page` with `impressions, clicks, position`, 2026-09-01..09 (before), 2026-09-10..18 (after).
- Vercel domain read-only inventory: `uat.directpilot.ir` marked **verified=true** and branch `UAT` under project `prj_w46jn80pmeOpoIZ5KZmQiY7GfKDl`. This is a domain-to-branch association, **NOT proof of an exact deployed SHA, alias freshness, browser acceptance, or correct response headers**.
- GitHub status of front-end `UAT` merge SHA `3275c73b3ef0e58132f2d6989f3efb57e1e15817`: `Vercel: success`, deployment URL `https://vercel.com/mohcenp-9857s-projects/directpilot-web/Bvq7zXSTgG9wQbvf19QXyoFhz2P7`. The authenticated Vercel deployment details/list were inaccessible (403 or 404 under current connected scope). Public UAT page and robots requests returned inaccessible through web tool. Do not label UAT alias deployment/browser SEO checks PASS.
- Public `https://directpilot.ir/pricing` HTML was retrievable; direct requests for both Production robots and sitemap through current web source were inaccessible. This is *not* proof those endpoints are down.

## Confirmed breakpoint in search impressions
For two equal, adjacent 9-day windows in daily **property-level** Web Search data:

| Window (inclusive) | Impressions | Average/day | Clicks |
|---|---:|---:|---:|
| 2026-09-01..2026-09-09 | 468 | 52.00 | 4 |
| 2026-09-10..2026-09-18 | 87 | 9.67 | 6 |

Daily impression average change = `(87 - 468) / 468 = -81.4103%` (both nine days). The step change begins **2026-09-10**: Sep 9 = 53, Sep 10 = 11 impressions. This is a temporal observation, **NOT** proof of a Google indexing penalty, a deployment regression, server outage, changed search demand or any single causal incident. Subsequent daily values vary materially (Sep 19 = 39, Oct 10 = 35, many days 0–4), so check data reliability, GSC filters and crawl diagnostics before attribution.

Page-dimension impressions over the *same* comparison windows (do **not** add URL rows to property-level totals; aggregation differs):

| Page | Sep 1–9 | Sep 10–18 | Note |
|---|---:|---:|---|
| `/blog/instagram-smart-direct` | 187 | 70 | Average position 37.83 -> 64.17, but query mix can shift |
| `/pricing` | 90 | 6 | Commercial page, steep exposure loss |
| `/instagram-comment-automation` | 69 | 7 | Core landing page |
| `/free-instagram-automation` | 25 | 9 | Paid conversion or trial intent |

Historical 28-day comparison already in `docs/seo/GSC_AUDIT_2026-10-18.md` (frontend `UAT`): Aug 21–Sep 17 = 917 impressions / 12 clicks; Sep 18–Oct 15 = 133 impressions / 11 clicks. This new breakpoint narrows *when* investigation should focus, without superseding the full-window analysis.

## Next action gates
1. Google Search Console **website UI** URL Inspection: homepage, pricing, blog smart-direct, comment landing, direct landing, free trial. Capture user vs Google canonical, status/reason, robots, last crawl and page fetch, together with Pages report, security/manual actions, and sitemap fetch.
2. Correlate Sep 9–10 with **actual Production deploy/redirect/header history**, DNS incidents and server availability. Do not infer causation from chronology alone.
3. Verify exact deployed Git SHA and READY status for **the UAT alias** (not just branch-assigned domain or GitHub Vercel SUCCESS), authenticated route tests, UAT noindex and sitemap exclusion. Vercel deployment access currently blocked by connector permission/scope; Browser connector lacks an originating browser context.
4. Promotion to Production requires explicit owner approval and exact Production `SEO_INDEXING_ENABLED=true` / `NEXT_PUBLIC_SITE_URL` / project-id preflight; never accidentally ship NOINDEX. No code or configuration change in this investigation.
5. Preserve all existing Owner-accepted work and historical test evidence; do not reopen closed P0/P1/P2 tasks without regression evidence.

**State:** DATA BREAKPOINT VERIFIED / ROOT CAUSE UNKNOWN / UAT ALIAS RELEASE UNVERIFIED / PRODUCTION UNCHANGED. Owner signoff for any new Production SEO release: NOT REQUESTED / NOT GRANTED.

## 2026-10-18 follow-up — first production deploy correlation + device segmentation

### Verified Vercel events (read-only)
The actual Vercel team audit event stream (project `directpilot-web`, `prj_w46jn80pmeOpoIZ5KZmQiY7GfKDl`) reports:
- Previous observed Production deploy **2026-09-06 11:49:44 UTC**, source Git `7d909ea` on `main`, aliases assigned 11:51:43 UTC.
- Next observed Production deploy **2026-09-09 10:01:33 UTC**, source Git `d98a524` on `main`, aliases assigned **10:03:33 UTC**.
- Vercel event search for **2026-09-10..11 UTC returned 0 events**. Subsequent Production deployments recorded Sep 12 onward. These audit windows do not prove all external outages/redirects or the exact live HTTP headers at historical time.
- GitHub comparison `7d909ea..d98a524` shows exactly **one commit and seven changed files**, all related to Automation Rules UI, API types, portal and tests. **No changes** to `app/robots.ts`, `app/sitemap.ts`, `lib/seo.ts`, `app/layout.tsx` or `next.config.ts`; read-only fetch confirmed **identical blob SHAs** for those five files at both commits. Thus direct SEO source edit in Sep 9 deployment is **NOT SUPPORTED**, while build/runtime/environment and external factors have NOT been independently excluded. Event preceded impression breakpoint, but temporal proximity **is not proof of causation**.

### New device and geography breakdown, equal nine-day windows

| Search dimension | Sep 1–9 impressions | Sep 10–18 impressions | Change |
|---|---:|---:|---:|
| Desktop | **409** | **30** | **-92.7%** |
| Mobile | **59** | **57** | **-3.4%** |
| Iran | **457** | **72** | **-84.2%** |
| Other countries combined | **11** | **15** | **+36.4%** (tiny count, avoid interpretation) |

**Confirmed:** Loss is concentrated in DESKTOP and Iran, but dimensions overlap and cannot be treated as independent causes. Desktop day-level Web Search impressions fell **47 on Sep 9 → 4 on Sep 10**; mobile **6 → 7**. Desktop average position over the windows changed **27.48 → 35.67**; mobile **64.46 → 66.49**. Position averages are impression-weighted and reflect changing query mix; do NOT attribute all change to ranking alone. Search query dimension can omit anonymized terms.

### UAT routing and live content limitations
- Direct Vercel audit events show 2026-10-18 05:16:48 UTC deployment of frontend `3275c73` on `UAT` and a 05:17:31 UTC event assigning **two aliases** to a deployment hostname. Together with GitHub Vercel SUCCESS, this supports that UAT branch build was deployed, but the **names of the two aliases are not exposed** in this event and the exact custom-domain-to-deployment mapping remains unverified. A separate Vercel domain-project query confirms `uat.directpilot.ir` is verified and branch-bound to `UAT`. Direct get_deployment/list_deployments/get_alias returned 403/404 in connector scope; browser connector lacked an originating browser context; direct web fetch of UAT pages inaccessible. Continue to mark custom UAT alias/browser/noindex **UNVERIFIED**.
- On **2026-10-18** independent public HTML fetches of Production `/`, `/pricing`, `/instagram-comment-automation`, `/free-instagram-automation` and blog succeeded. Live `/free-instagram-automation` describes **three-day trial**, consistent with current product policy. A *stale search-index snippet* displayed an older claim of perpetual free plan; **that snippet is not the current production page text**, so do not record a confirmed live free/trial contradiction from it. Production robots.txt and sitemap.xml HTTP responses could not be captured through available web and container source; error from fetch tools is NOT evidence of public outage or deindexing.
- The currently connected GSC Wizard URL Inspection/quota APIs responded **payment_required**. Windsor.ai can read connected Search Analytics and Sitemaps but **does not expose Google URL Inspection verdict, user/google canonical, robots or last crawl**. Cannot confirm URL indexing verdict or crawl reason without an authorized account's Google Search Console UI or another approved Inspection-capable connection.

### Updated priority
1. Inspect **desktop** vs mobile Search Console page+query comparisons specifically around Sep 9–10, and full Search Console Pages/URL Inspection to confirm crawl/index/canonical status; review historical Production Vercel runtime/environment and Google service interruptions if credible evidence emerges.
2. Independently verify UAT custom alias exact commit SHA and UAT `Disallow: /` / empty sitemap (source logic checks only); maintain SEO Production release flag safeguard.
3. Do not deploy SEO changes to Production or change robots/canonical based solely on Sep 9 deployment coincidence.
