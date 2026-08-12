# Iranian Payment Provider Research

## RC decision

The guaranteed first-pilot provider is `ManualCardTransferProvider`. It avoids
blocking the MVP on external merchant/KYC onboarding while retaining human
approval and an auditable subscription transition.

## Online gateway candidates

Candidate official services include ZarinPal and IDPay. During this review the
official documentation endpoints were unavailable to the automated research
environment (search returned no indexed primary result and the IDPay document
request timed out). Therefore no current fee, settlement, sandbox, KYC or domain
claim is treated as verified and no online provider is integrated.

Before choosing a P1 gateway, an operator must verify directly with the
provider's current official material:

- legal/business and identity onboarding requirements;
- production domain, trust-symbol and callback requirements;
- server-side create/verify API and signed callback behavior;
- sandbox availability and idempotency semantics;
- fee schedule, settlement timing and failure/refund operations;
- contractual permission for DirectPilot's business model.

Unofficial card-transfer scraping or personal-banking automation is explicitly
out of scope. A future adapter must implement the existing payment-provider
boundary without changing order, approval or entitlement invariants.
