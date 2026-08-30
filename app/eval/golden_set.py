
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GoldenQuestion:
    id: str
    question: str
    should_be_answerable: bool
    expected_source: str | None = None
    expected_keywords: list[str] = field(default_factory=list)
    reference_answer: str | None = None


GOLDEN_SET: list[GoldenQuestion] = [
    GoldenQuestion("q01", "How do I reset my password?", True, "password_reset_policy",
                    ["settings", "security", "reset password"],
                    "Go to Settings, then Security, then Reset Password. Enter your account email "
                    "and a reset link will be sent; the link expires 24 hours after it's issued."),
    GoldenQuestion("q02", "What are the password requirements?", True, "password_reset_policy",
                    ["10 characters", "number", "symbol"],
                    "Passwords must be at least 10 characters long and include one number and one "
                    "symbol. A new password cannot match any of the last 5 passwords used."),
    GoldenQuestion("q03", "What happens after 5 failed login attempts?", True, "password_reset_policy",
                    ["locked", "15 minutes"],
                    "The account is locked for 15 minutes. A password reset link can still be "
                    "requested during that window and will unlock the account immediately once used."),

    GoldenQuestion("q04", "How does SSO login work for enterprise accounts?", True, "sso_enterprise_login",
                    ["identity provider"],
                    "Organizations on the Enterprise plan can enable SSO through an identity provider "
                    "such as Okta, Azure AD, or Google Workspace. Once enabled, all members must log "
                    "in through the identity provider's page instead of the standard email/password screen."),
    GoldenQuestion("q05", "Can I reset my password if my organization uses SSO?", True, "sso_enterprise_login",
                    ["identity provider"],
                    "No. There is no in-app password reset for SSO accounts, since the identity "
                    "provider manages the password, not the platform. You must contact your "
                    "organization's IT administrator instead."),
    GoldenQuestion("q06", "How do I enable SSO for my organization?", True, "sso_enterprise_login",
                    ["organization settings", "metadata"],
                    "An account owner on the Enterprise plan can enable SSO from Organization "
                    "Settings, then Security, then Single Sign-On, using the identity provider's "
                    "metadata URL or XML file."),

    GoldenQuestion("q07", "How do I set up two-factor authentication?", True, "two_factor_authentication",
                    ["qr code", "authenticator"],
                    "Go to Settings, then Security, then Two-Factor Authentication, and scan the QR "
                    "code with an authenticator app. Enter the 6-digit code shown to confirm setup."),
    GoldenQuestion("q08", "How many backup codes do I get for 2FA?", True, "two_factor_authentication",
                    ["10", "backup codes"],
                    "You are given 10 single-use backup codes after enabling 2FA."),
    GoldenQuestion("q09", "What happens if I lose access to my authenticator app and have no backup codes?", True,
                    "two_factor_authentication", ["contact support", "48 hours"],
                    "Contact support with proof of account ownership. Account recovery in this case "
                    "can take up to 48 hours for security review."),

    GoldenQuestion("q10", "What is the API rate limit for free tier accounts?", True, "api_rate_limits",
                    ["60", "5,000"],
                    "Free tier accounts are limited to 60 requests per minute and 5,000 requests per day."),
    GoldenQuestion("q11", "What happens when I exceed the API rate limit?", True, "api_rate_limits",
                    ["429", "retry-after"],
                    "Requests beyond the limit return a 429 status code with a Retry-After header "
                    "indicating how many seconds to wait before retrying."),
    GoldenQuestion("q12", "How can I request a higher API rate limit?", True, "api_rate_limits",
                    ["pro tier", "business day"],
                    "Pro tier customers can request a temporary rate limit increase by contacting "
                    "support with their expected peak usage; increases are typically approved within "
                    "one business day."),

    GoldenQuestion("q13", "What does a 401 error mean?", True, "api_error_codes",
                    ["api key", "invalid"],
                    "A 401 Unauthorized error means the API key is missing, invalid, or expired. "
                    "Generate a new key from Developer Settings, then API Keys."),
    GoldenQuestion("q14", "What should I do if I get a 500 error?", True, "api_error_codes",
                    ["status page", "x-request-id"],
                    "500 errors are automatically logged and investigated. If it persists for more "
                    "than a few minutes, check the status page or contact support with the "
                    "X-Request-Id header value from the failed response."),
    GoldenQuestion("q15", "What does a 403 error mean?", True, "api_error_codes",
                    ["forbidden", "scope"],
                    "A 403 Forbidden error means the API key is valid but doesn't have permission for "
                    "this action; check that the key has the correct scopes assigned."),

    GoldenQuestion("q16", "When am I charged for my subscription?", True, "billing_cycle_faq",
                    ["signup", "calendar day"],
                    "Monthly plans are charged on the same calendar day each month as the original "
                    "signup date. Annual plans are charged once per year on the signup anniversary."),
    GoldenQuestion("q17", "What happens if my payment fails?", True, "billing_cycle_faq",
                    ["3 times", "7 days"],
                    "A failed payment is retried 3 times over 7 days. If all retries fail, the "
                    "account is downgraded to the free tier and an email is sent with a link to "
                    "update the payment method and restore access."),
    GoldenQuestion("q18", "What happens if I upgrade my plan in the middle of a billing cycle?", True,
                    "billing_cycle_faq", ["prorated"],
                    "Upgrading mid-cycle charges a prorated amount immediately for the remainder of "
                    "the current cycle, then bills the full new plan price on the next regular billing date."),

    GoldenQuestion("q19", "Can I get a refund on my annual plan after 30 days?", True, "refund_policy",
                    ["30 days"],
                    "No. Annual plans are refundable on a prorated basis only within the first 30 "
                    "days of the annual term; after that, no refund is issued for the remainder of the year."),
    GoldenQuestion("q20", "How do I request a refund?", True, "refund_policy",
                    ["billing", "payment history"],
                    "Go to Billing, then Payment History, select the charge, and click Request "
                    "Refund. Refunds are processed to the original payment method within 5-10 business days."),
    GoldenQuestion("q21", "What is the standard refund window?", True, "refund_policy",
                    ["14 days"],
                    "Refunds are available within 14 days of the original charge for any paid plan. "
                    "Requests after 14 days are evaluated case-by-case and are not guaranteed."),

    GoldenQuestion("q22", "How do I delete my account?", True, "account_deletion_policy",
                    ["settings", "delete account"],
                    "Go to Settings, then Account, then Delete Account. You'll be asked to confirm "
                    "via a link sent to your registered email address."),
    GoldenQuestion("q23", "What happens during the grace period after I delete my account?", True,
                    "account_deletion_policy", ["30-day", "restored"],
                    "Deleted accounts enter a 30-day grace period during which the account can be "
                    "restored simply by logging back in. After 30 days, all data is permanently deleted."),
    GoldenQuestion("q24", "Are my billing records deleted when I delete my account?", True,
                    "account_deletion_policy", ["7 years", "retained"],
                    "No. Billing records required for tax and legal compliance are retained "
                    "separately for 7 years, but are no longer linked to the active account."),

    # Out-of-corpus -- correct behavior is insufficient_context=True, no reference answer applicable
    GoldenQuestion("q25", "How do I export my account data as a CSV file?", False),
    GoldenQuestion("q26", "What is the current mobile app version number?", False),
    GoldenQuestion("q27", "Do you support login via LDAP?", False),
    GoldenQuestion("q28", "What is the price of the enterprise plan?", False),
    GoldenQuestion("q29", "How do I integrate with Slack?", False),
]
