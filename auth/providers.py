from core.environment import env

OAUTH_PROVIDERS = {
    "google": {
        "client_id": env.google_client_id,
        "client_secret": env.google_secret,
        "authorize_url": "https://accounts.google.com/o/oauth2/auth",
        "access_token_url": "https://accounts.google.com/o/oauth2/token",
        "redirect_uri": env.oauth_redirect_uri,
    },
    "facebook": {
        "client_id": env.facebook_client_id,
        "client_secret": env.facebook_secret,
        "authorize_url": "https://www.facebook.com/v8.0/dialog/oauth",
        "access_token_url": "https://graph.facebook.com/v8.0/oauth/access_token",
        "redirect_uri": env.oauth_redirect_uri,
    },
}
