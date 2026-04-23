# Zoom Live Integration Guide

## What this app already supports
- a Zoom OAuth authorization URL endpoint
- a callback endpoint for OAuth code exchange
- a recording completion webhook endpoint at `/integrations/zoom/recording-complete`
- a recorded-class library inside the school portal

## What you need from Zoom
1. A Zoom app in the Zoom Developer portal
2. OAuth credentials for user-authorized meeting scheduling
3. Event subscriptions for recording completion if you want auto-sync
4. Cloud Recording enabled in the connected Zoom account

## Recommended production setup
Use user-authorized OAuth for teachers/admins who will schedule meetings. Use the recording completion webhook so completed classes automatically create entries in the recorded class library.

## Environment variables
Set these in `.env`:
- `ZOOM_CLIENT_ID`
- `ZOOM_CLIENT_SECRET`
- `ZOOM_REDIRECT_URI=https://school.yourdomain.com/integrations/zoom/callback`
- `ZOOM_WEBHOOK_SECRET_TOKEN`
- `APP_BASE_URL=https://school.yourdomain.com`

## Zoom portal settings
In your Zoom app configuration, add:
- Redirect URL: `https://school.yourdomain.com/integrations/zoom/callback`
- Event notification endpoint: `https://school.yourdomain.com/integrations/zoom/recording-complete`

## Important note
The current project contains the integration hooks and webhook ingest route, but you still need to install your real credentials and test them against your own Zoom tenant before production use.

## Recorded class flow
1. Teacher schedules and runs the class in Zoom
2. Zoom cloud recording completes
3. Zoom sends the recording-complete event to Aureline
4. Aureline stores the recording URL against the course
5. Students in the matching class can replay the class from the recordings page
