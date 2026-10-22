# CameVision

Camemake phone app for CameVision Ego Single Sensor (CV-EGO01-SS). One camera, one IMU.

English is the first language. Every sentence the user sees is in `app/src/main/res/values/strings.xml`, so more languages can be added as `values-xx` later.

## Two modes

**Standalone.** Bluetooth starts and stops a recording on the microSD card. This phone copies the files and uploads them to the server in Setup. When the card is nearly full, the phone shows a warning and a notification.

**Online.** The camera still writes the recording to the card, and uploads it over the camera Wi-Fi to that same server. The card is the buffer if the network drops.

Setup holds the server address. The field starts as `https://server.example.com/camevision/v1`. Replace it. Leave the token empty when the server is open. The contract is `server.template.json`.

Camera Wi-Fi in Setup is sent to the camera over Bluetooth and written to `wpa_camevision.conf`.

## On the card

```
<card>/camevision/sessions/20261023T160102Z/
  session.json
  imu0.csv
  cam0/video.mp4
```

`video.mp4` is a full-resolution H.264 recording (1920×1200 on SC233HGS, 1400×1600 on MIRA220). The 10-second preview is a separate live image, not the recording.

`imu0.csv` is `t_unix_ns,t_mono_ns,ax,ay,az,gx,gy,gz`. Accel is m/s². Gyro is deg/s.

The camera service is `tools/camevision_agent.py`. It listens on Bluetooth as **CameVision Single** and on `http://<camera>:8090`.

## Build

Open `android/` in Android Studio, or:

```
cd android
gradlew.bat assembleDebug
```

The debug APK is `app/build/outputs/apk/debug/app-debug.apk`.
