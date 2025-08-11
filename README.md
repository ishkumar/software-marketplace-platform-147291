# Project Repository

This is the initial README file for the project.

## Social Login Provider Setup

To enable social authentication (Google, GitHub, Facebook, LinkedIn):

1. Set the corresponding client IDs and secrets in your `.env` file. See `.env.example` for variable names.
2. The following providers are supported out of the box:
   * Google
   * GitHub
   * Facebook
   * LinkedIn

To add additional providers (Twitter, Microsoft, etc.):
- For Django Allauth: Add `allauth.socialaccount.providers.<providername>` to `INSTALLED_APPS` in `config/settings.py`.
- Update the `SOCIALACCOUNT_PROVIDERS` dict in settings.py.
- Update frontend `SocialLoginButtons.js` to allow redirects to the new provider.

Backend OAuth endpoints will be available under `/social/login/<provider>/`. For full list, see `/social/` or `/accounts/`.

## Environment variables

Providers use keys like `GOOGLE_CLIENT_ID`, `GITHUB_CLIENT_ID`, `FACEBOOK_CLIENT_ID`, `LINKEDIN_CLIENT_ID` etc., in your .env file.
