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
    val product: String = "",
    val sku: String = "",
    val profile: String = "single",
    val title: String = "",
    val fw: String = "",
    val protocol: Int = 0,
    val sensors: Int = 1,
    val sensor: String = "",
    val imuCount: Int = 1,
    val nativeW: Int = 0,
    val nativeH: Int = 0,
    val boardId: String = "",
)

fun CameraStatus.displayTitle(): String = title.trim()

fun frontTitle(connected: Boolean, status: CameraStatus, bleName: String = ""): String {
    if (!connected) return "CameVision"
    return status.title.trim().ifBlank { bleName.trim() }.ifBlank { "CameVision" }
}

fun CameraStatus.isStereo(): Boolean = profile == "stereo" || profile == "ego" || profile == "dual" || sensors >= 2

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
    val host: String = "192.168.1.72",
    val address: String = "",
    val qr: String = "camevision-trigger",
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

const val DEFAULT_HOST = "192.168.1.72"

fun cameraBase(ip: String, hostField: String): String {
    val raw = ip.ifBlank { hostField }.ifBlank { DEFAULT_HOST }.trim()
    val bare = raw.removePrefix("http://").removePrefix("https://").trimEnd('/')
    val hostPort = bare.substringBefore("/")
    if (hostPort.isBlank()) return "http://$DEFAULT_HOST:8090"
    val withPort = if (hostPort.contains(":")) hostPort else "$hostPort:8090"
    return "http://$withPort"
}
