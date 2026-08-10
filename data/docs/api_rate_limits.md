# API Rate Limits

## Default limits

Free tier accounts are limited to 60 requests per minute and 5,000
requests per day. Pro tier accounts are limited to 600 requests per
minute and 100,000 requests per day. Enterprise limits are negotiated
per contract.

## Rate limit headers

Every API response includes `X-RateLimit-Limit`, `X-RateLimit-Remaining`,
and `X-RateLimit-Reset` headers so clients can track their usage
without guessing.

## What happens when you exceed the limit

Requests beyond the limit return a 429 status code with a `Retry-After`
header indicating how many seconds to wait before retrying. Repeated
429s within a short window may trigger a temporary IP-level throttle
in addition to the account-level limit.

## Requesting a higher limit

Pro tier customers can request a temporary rate limit increase by
contacting support with their expected peak usage. Increases are
typically approved within one business day.
