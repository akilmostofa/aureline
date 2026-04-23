class ZoomService:
    def __init__(self, config):
        self.config = config

    def authorization_url(self):
        client_id = self.config.get("ZOOM_CLIENT_ID") or "your-zoom-client-id"
        redirect_uri = self.config.get("ZOOM_REDIRECT_URI") or "https://example.com/integrations/zoom/callback"
        return (
            "https://zoom.us/oauth/authorize"
            f"?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"
        )

    def exchange_code_for_token(self, code):
        return {
            "ok": bool(code),
            "message": "Replace with live OAuth token exchange.",
            "code": code,
        }
