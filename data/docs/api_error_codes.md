# API Error Code Reference

## 400 Bad Request

The request body failed schema validation. The response includes a
`details` array listing which fields failed and why.

## 401 Unauthorized

The API key is missing, invalid, or expired. Generate a new key from
Developer Settings then API Keys.

## 403 Forbidden

The API key is valid but does not have permission for this action.
Check that the key has the correct scopes assigned.

## 429 Too Many Requests

The account has exceeded its rate limit. See the API Rate Limits
document for the retry behavior and how to request a higher limit.

## 500 Internal Server Error

An unexpected error occurred on our end. These are automatically
logged and investigated. If it persists for more than a few minutes,
check the status page or contact support with the `X-Request-Id`
header value from the failed response.
