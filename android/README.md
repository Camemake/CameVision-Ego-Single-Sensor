# CameVision

Android app for CameVision cameras. One install talks to Ego Single, Ego (two sensors), and later CameVision boards. The connected camera sends its own title, firmware, and sensor count. The home screen shows **CameVision** until a board is linked, then it shows that board’s title.

This repository is the phone app only. Device firmware lives in the Ego and Ego Single Sensor repos.

English is the first language. Every sentence on screen is in `app/src/main/res/values/strings.xml`.

## What the app does

The camera itself has three ways to work. This app is the last two. USB **Camemake** UVC is not an app mode — plug the camera into a computer and open that computer’s camera app.

1. **Standalone** — Bluetooth starts and stops a full-resolution recording on the microSD card. The phone can copy those files and upload them to the server in Setup.
2. **Server** — Bluetooth still starts and stops the recording. The camera also uploads over its own Wi-Fi. The card is the buffer if the network drops.

Preview (**Position**) and record always go over Bluetooth. Wi-Fi is only for server / online upload.

### Record

- Start recording / Recording / Stop recording
- Live JPEG preview over Bluetooth
- Optional QR trigger shown on this page (text is set in Setup)

### Card

- Free and used space
- List, delete, or clear recordings
- Warning and a notification when the card is nearly full (default 85%)

### Setup

- Pair and forget the camera over Bluetooth
- Server address and optional token
- Camera Wi-Fi (sent to the board over Bluetooth)
- About: board title, SKU, firmware, sensor count, protocol

## Boards

The app does not guess Single vs Ego. After connect it reads the board:

| Field | Meaning |
|---|---|
| `title` | Shown on the home screen |
| `sku` / `product` | Board stock keeping unit |
| `fw` | Firmware version |
| `sensors` / `profile` | One camera or two |
| `protocol` | JSON protocol revision |

Scan matches an advertised name containing `CameVision`, or GATT service `6c9a0001-1a6f-4e84-8a00-63616d657631`.

## On the card

```
<card>/camevision/sessions/<YYYYMMDDTHHMMSSZ>/
  session.json
  imu0.csv
  cam0/video.mp4
  COMPLETE
```

`video.mp4` is the full-resolution H.264 recording (1400×1600 on MIRA220, 1920×1200 on SC233HGS). Position preview is a separate live JPEG over Bluetooth, not the recorded file.

`imu0.csv` is `t_unix_ns,t_mono_ns,ax,ay,az,gx,gy,gz`. Accel is m/s². Gyro is deg/s.

## Server

Setup starts as `https://server.example.com/camevision/v1`. Replace it. Leave the token empty when the server is open. The contract is `server.template.json`.

```
POST /sessions
POST /sessions/{id}/files
POST /sessions/{id}/complete
```

Headers: `X-CameVision-Product`, `X-CameVision-Session`, `X-CameVision-Path`.

## Build

Open this folder in Android Studio, or:

```
gradlew.bat assembleDebug
```

Debug APK: `app/build/outputs/apk/debug/app-debug.apk`

Requires Android 7 (API 24) or newer. Bluetooth is used for control and preview.

## Release

GitHub release **0.1** is this debug build. Source is in this repository.
