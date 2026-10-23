package eu.camemake.camevision

import org.json.JSONArray
import org.json.JSONObject

object Protocol {
    val service: java.util.UUID = java.util.UUID.fromString("6c9a0001-1a6f-4e84-8a00-63616d657631")
    val command: java.util.UUID = java.util.UUID.fromString("6c9a0002-1a6f-4e84-8a00-63616d657631")
    val info: java.util.UUID = java.util.UUID.fromString("6c9a0003-1a6f-4e84-8a00-63616d657631")
    val frame: java.util.UUID = java.util.UUID.fromString("6c9a0004-1a6f-4e84-8a00-63616d657631")
    val cccd: java.util.UUID = java.util.UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")
}

sealed class InfoEvent {
    data class Status(val status: CameraStatus) : InfoEvent()
    data class Sessions(val items: List<SessionRow>) : InfoEvent()
    data class Wifi(val items: List<WifiNet>) : InfoEvent()
    data class Ack(val cmd: String, val ok: Boolean, val error: String, val session: String = "") : InfoEvent()
    data class Hello(val name: String) : InfoEvent()
}

fun parseInfo(text: String): InfoEvent? {
    val obj = try {
        JSONObject(text)
    } catch (_: Exception) {
        return null
    }
    return when (obj.optString("t")) {
        "status" -> InfoEvent.Status(parseStatus(obj))
        "sessions" -> InfoEvent.Sessions(parseSessionArray(obj.optJSONArray("items")))
        "wifi" -> InfoEvent.Wifi(parseWifi(obj.optJSONArray("items")))
        "ack" -> InfoEvent.Ack(
            obj.optString("cmd"),
            obj.optBoolean("ok"),
            obj.optString("error"),
            obj.optString("session"),
        )
        "hello" -> InfoEvent.Hello(obj.optString("name").ifBlank { obj.optString("title").ifBlank { "CameVision" } })
        else -> null
    }
}

fun parseStatus(obj: JSONObject): CameraStatus = CameraStatus(
    recording = obj.optBoolean("recording"),
    mode = modeOf(obj.optString("mode")),
    session = obj.optString("session"),
    frames = obj.optInt("frames"),
    width = obj.optInt("width"),
    height = obj.optInt("height"),
    imuHz = obj.optDouble("imu_hz"),
    sdTotal = obj.optLong("sd_total"),
    sdUsed = obj.optLong("sd_used"),
    sdFree = obj.optLong("sd_free"),
    sdWarn = obj.optBoolean("sd_warn"),
    card = obj.optBoolean("card"),
    wifi = obj.optString("wifi").ifBlank { "down" },
    ssid = obj.optString("ssid"),
    ip = obj.optString("ip"),
    pending = obj.optInt("pending"),
    sent = obj.optInt("sent"),
    preview = obj.optBoolean("preview"),
    error = obj.optString("error"),
    product = obj.optString("product"),
    sku = obj.optString("sku").ifBlank { obj.optString("product") },
    profile = obj.optString("profile").ifBlank { "single" },
    title = obj.optString("title"),
    fw = obj.optString("fw"),
    protocol = obj.optInt("protocol"),
    sensors = obj.optInt("sensors", 1).coerceAtLeast(1),
    sensor = obj.optString("sensor"),
    imuCount = obj.optInt("imu", 1).coerceAtLeast(0),
    nativeW = obj.optInt("native_w"),
    nativeH = obj.optInt("native_h"),
    boardId = obj.optString("board"),
)

fun parseSessions(text: String): List<SessionRow> {
    val obj = try {
        JSONObject(text)
    } catch (_: Exception) {
        return emptyList()
    }
    return parseSessionArray(obj.optJSONArray("items"))
}

private fun parseWifi(array: JSONArray?): List<WifiNet> {
    if (array == null) return emptyList()
    return buildList {
        for (i in 0 until array.length()) {
            val item = array.optJSONObject(i) ?: continue
            val ssid = item.optString("ssid")
            if (ssid.isBlank()) continue
            add(WifiNet(ssid, item.optInt("rssi"), item.optBoolean("secure")))
        }
    }
}

private fun parseSessionArray(array: JSONArray?): List<SessionRow> {
    if (array == null) return emptyList()
    return buildList {
        for (i in 0 until array.length()) {
            val item = array.optJSONObject(i) ?: continue
            val id = item.optString("id")
            if (id.isBlank()) continue
            add(
                SessionRow(
                    id = id,
                    frames = item.optInt("frames"),
                    bytes = item.optLong("bytes"),
                    mode = item.optString("mode"),
                    started = item.optString("started"),
                    sent = item.optBoolean("sent"),
                ),
            )
        }
    }
}

class InfoAssembler {
    private var id = -1
    private val parts = ArrayList<ByteArray>()

    fun push(packet: ByteArray): String? {
        if (packet.size < 2) return null
        val flags = packet[0].toInt() and 0xff
        val mid = packet[1].toInt() and 0xff
        val first = flags and 1 != 0
        val last = flags and 2 != 0
        if (first || mid != id) {
            id = mid
            parts.clear()
        }
        parts.add(packet.copyOfRange(2, packet.size))
        if (!last) return null
        val size = parts.sumOf { it.size }
        val out = ByteArray(size)
        var cursor = 0
        for (part in parts) {
            part.copyInto(out, cursor)
            cursor += part.size
        }
        parts.clear()
        return out.toString(Charsets.UTF_8)
    }
}

class FrameAssembler {
    private var seq = -1
    private var count = 0
    private val chunks = HashMap<Int, ByteArray>()

    fun push(packet: ByteArray): ByteArray? {
        if (packet.size < 6) return null
        val nextSeq = ((packet[0].toInt() and 0xff) shl 8) or (packet[1].toInt() and 0xff)
        val index = ((packet[2].toInt() and 0xff) shl 8) or (packet[3].toInt() and 0xff)
        val nextCount = ((packet[4].toInt() and 0xff) shl 8) or (packet[5].toInt() and 0xff)
        if (nextSeq != seq) {
            seq = nextSeq
            count = nextCount
            chunks.clear()
        }
        chunks[index] = packet.copyOfRange(6, packet.size)
        if (count <= 0 || chunks.size < count) return null
        var size = 0
        for (i in 0 until count) {
            val chunk = chunks[i] ?: return null
            size += chunk.size
        }
        val out = ByteArray(size)
        var cursor = 0
        for (i in 0 until count) {
            val chunk = chunks[i] ?: return null
            chunk.copyInto(out, cursor)
            cursor += chunk.size
        }
        chunks.clear()
        return out
    }
}
