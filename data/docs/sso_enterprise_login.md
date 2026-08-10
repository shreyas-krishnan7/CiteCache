# SSO and Enterprise Login

## How enterprise SSO login works

Organizations on the Enterprise plan can enable single sign-on (SSO)
through an identity provider such as Okta, Azure AD, or Google
Workspace. Once enabled, all members of that organization must log in
through the identity provider's login page — the standard email and
password login screen is disabled for that organization.

## Resetting access for SSO accounts

There is no in-app password reset for SSO accounts, because the
password itself is managed entirely by your organization's identity
provider, not by us. If you cannot log in, contact your organization's
IT administrator to reset your credentials in the identity provider
directly. We cannot reset an SSO user's password on our end.

## Enabling SSO for your organization

An account owner on the Enterprise plan can enable SSO from
Organization Settings then Security then Single Sign-On. You will need
your identity provider's metadata URL or XML file to complete setup.

## Disabling SSO

Disabling SSO reverts all members to standard email and password
login. Members who never had a password set (because they only ever
logged in via SSO) will need to use the "forgot password" flow once
to set one, exactly like a new consumer account.
