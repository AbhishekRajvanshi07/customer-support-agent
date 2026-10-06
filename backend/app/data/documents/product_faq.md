# Acme Cloud Suite — Support Knowledge Base

## Billing & Subscriptions
Acme Cloud Suite is billed monthly per active seat. Invoices are generated
on the 1st of each month and are due within 15 days. Customers on the
Enterprise plan can switch to annual billing for a 15% discount by
contacting their account manager. Downgrading a plan takes effect at the
start of the next billing cycle; upgrades take effect immediately and are
billed pro-rata.

## Password Reset
Users can reset their password from the login page by selecting
"Forgot password." A reset link is emailed and expires after 30 minutes.
If a user does not receive the email, ask them to check their spam
folder and confirm their account email address is correct in
Settings > Account. SSO-enabled organizations must reset passwords
through their identity provider, not through Acme directly.

## API Rate Limits
The standard API tier allows 100 requests per minute per API key.
The Enterprise tier allows 1,000 requests per minute and supports
burst limits of up to 2,000 requests for short periods. Requests
beyond the limit receive an HTTP 429 response with a `Retry-After`
header indicating when to retry.

## Data Export
Customers can export their data at any time from Settings > Data Export.
Exports are generated as a downloadable ZIP containing CSV files and
are available for 7 days before the download link expires. Full account
data exports (for offboarding) can be requested from support and are
typically ready within 24 hours.

## Uptime & Incidents
Acme Cloud Suite targets 99.9% monthly uptime for Enterprise customers,
as described in the Service Level Agreement. Live incident status is
published at status.acme.example.com. Enterprise customers affected by
a qualifying outage may request service credits per the SLA terms.

## Cancellation Policy
Customers may cancel at any time from Settings > Billing. Cancellation
takes effect at the end of the current billing period, and no partial
refunds are issued for the remainder of that period. Data is retained
for 30 days after cancellation before permanent deletion.
