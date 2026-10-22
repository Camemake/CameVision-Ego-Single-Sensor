package eu.camemake.camevision

enum class CaptureMode { Standalone, Online }

fun CaptureMode.wire(): String = if (this == CaptureMode.Online) "online" else "standalone"

fun modeOf(raw: String?): CaptureMode =
    if (raw == "online") CaptureMode.Online else CaptureMode.Standalone

const val SERVER_TEMPLATE = "https://server.example.com/camevision/v1"

fun isServerTemplate(url: String): Boolean {
    val host = url.trim()
    return host.isEmpty() || "server.example.com" in host
}

data class CameraStatus(
    val recording: Boolean = false,
    val mode: CaptureMode = CaptureMode.Standalone,
    val session: String = "",
    val frames: Int = 0,
    val width: Int = 0,
    val height: Int = 0,
    val imuHz: Double = 0.0,
    val sdTotal: Long = 0,
    val sdUsed: Long = 0,
    val sdFree: Long = 0,
    val sdWarn: Boolean = false,
    val card: Boolean = false,
    val wifi: String = "down",
    val ssid: String = "",
    val ip: String = "",
    val pending: Int = 0,
    val sent: Int = 0,
    val preview: Boolean = false,
    val error: String = "",
)

data class SessionRow(
    val id: String,
    val frames: Int,
    val bytes: Long,
    val mode: String,
    val started: String,
    val sent: Boolean,
)

data class FoundDevice(
    val name: String,
    val address: String,
    val rssi: Int,
)

data class AppConfig(
    val server: String = SERVER_TEMPLATE,
    val token: String = "",
    val ssid: String = "",
    val psk: String = "",
    val warn: Int = 85,
    val mode: CaptureMode = CaptureMode.Standalone,
    val host: String = "",
    val address: String = "",
)

data class WifiNet(
    val ssid: String,
    val rssi: Int,
    val secure: Boolean,
)

data class LinkState(
    val transport: String = "",
    val name: String = "",
    val status: CameraStatus = CameraStatus(),
    val sessions: List<SessionRow> = emptyList(),
    val scanning: Boolean = false,
    val found: List<FoundDevice> = emptyList(),
    val networks: List<WifiNet> = emptyList(),
    val paired: Boolean = false,
)

data class TransferState(
    val running: Boolean = false,
    val done: Int = 0,
    val total: Int = 0,
    val note: String = "",
    val error: String = "",
)

fun cameraBase(ip: String, hostField: String): String {
    val raw = ip.ifBlank { hostField }.trim()
    if (raw.isEmpty()) return ""
    val bare = raw.removePrefix("http://").removePrefix("https://").trimEnd('/')
    val hostPort = bare.substringBefore("/")
    val withPort = if (hostPort.contains(":")) hostPort else "$hostPort:8090"
    return "http://$withPort"
}
