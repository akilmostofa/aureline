# Payment Live Setup Guide

## What the app supports right now
- per-course fee configuration inside admin
- student checkout flow by request group
- PDF payment proof upload
- admin approval or rejection
- optional redirect button to an external payment portal for each provider

## Fastest real-life go-live path
If your merchant or payment provider gives you a hosted payment page or collection link, set these variables:
- `BKASH_PAYMENT_URL`
- `NAGAD_PAYMENT_URL`
- `CARD_PAYMENT_URL`
- `BANK_PAYMENT_URL`

Then the checkout page will show an **Open Payment Portal** button for that provider.

## Merchant-API path
The project already includes placeholders for merchant credentials:
- `BKASH_BASE_URL`, `BKASH_APP_KEY`, `BKASH_APP_SECRET`, `BKASH_USERNAME`, `BKASH_PASSWORD`
- `NAGAD_BASE_URL`, `NAGAD_MERCHANT_ID`, `NAGAD_PUBLIC_KEY`, `NAGAD_PRIVATE_KEY`

These are not enough by themselves. You also need production merchant onboarding, live endpoints, callback URLs, and provider-side approval.

## Recommended rollout
### Phase 1
Go live with hosted payment portal URLs plus PDF receipt upload and admin verification.

### Phase 2
After merchant approval, replace the hosted-link flow with direct API integration and webhook reconciliation.

## Student email copy
When a payment proof PDF is submitted, the app can email a copy to the requester if mail settings are configured.

## Minimum mail settings
- `MAIL_SERVER`
- `MAIL_PORT`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `MAIL_DEFAULT_SENDER`
