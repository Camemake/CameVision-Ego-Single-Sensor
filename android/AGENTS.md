# CameVision Android app

This folder is the phone app. It is not an Ego firmware tree. Do not flash boards or add UVC viewing.

CameVision is one app for multiple boards. English first. User-visible text stays in `app/src/main/res/values/strings.xml`. Disconnected title is **CameVision**. Connected title is the board’s own `title` (or BLE name). Do not guess Single vs Ego in the UI.

## Device has three options

1. **Camemake UVC** — USB webcam. Not an app screen.
2. **Standalone** — this app. Bluetooth start/stop. Files stay on the card. The phone can upload them.
3. **Server** (`online`) — this app. Same card files. The camera uploads over its Wi-Fi.

Preview and record use Bluetooth. HTTP `:8090` is server-mode fallback, not the primary control path.

## Must keep working

- Find a camera by name containing `CameVision` **or** GATT `6c9a0001-1a6f-4e84-8a00-63616d657631`.
- Start / stop recording over Bluetooth.
- Card tab: space, session list, clear, delete, nearly-full warning.
- Send through the phone to the server in Setup. Refuse while the host still contains `server.example.com`.
- Position preview over the BLE frame characteristic.
- About reads board title, firmware, SKU, sensors, protocol.
- Server contract: `server.template.json`.

## Card layout (`camevision-session-1`)

```
<card>/camevision/sessions/<YYYYMMDDTHHMMSSZ>/
  session.json
  imu0.csv
  cam0/video.mp4
  COMPLETE
```

## Do not

- Bind the app to one SKU in the launcher title.
- Persist or print a Wi-Fi PSK in git.
- Treat UVC as an app mode.
- Copy Ego stereo `My Recordings/.../episode/` as the phone layout.
