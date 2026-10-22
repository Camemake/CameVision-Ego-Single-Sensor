package eu.camemake.camevision

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import okhttp3.MediaType
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File
import java.util.concurrent.TimeUnit

object TransferHub {
    val state = MutableStateFlow(TransferState())

    @Volatile
    var cancel: Boolean = false
}

class SendService : Service() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val http = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(120, TimeUnit.SECONDS)
        .writeTimeout(120, TimeUnit.SECONDS)
        .build()
    private var working = false

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (working) return START_NOT_STICKY
        working = true
        TransferHub.cancel = false
        ensureChannel()
        val starting = note(getString(R.string.notif_sending), 0, 0, true)
        if (Build.VERSION.SDK_INT >= 29) {
            startForeground(NOTIF_ID, starting, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
        } else {
            startForeground(NOTIF_ID, starting)
        }
        val base = intent?.getStringExtra(EXTRA_BASE).orEmpty()
        val session = intent?.getStringExtra(EXTRA_SESSION).orEmpty()
        val deleteAfter = intent?.getBooleanExtra(EXTRA_DELETE, false) == true
        val lock = (getSystemService(POWER_SERVICE) as PowerManager)
            .newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "camevision:send")
        lock.acquire(30 * 60 * 1000L)
        scope.launch {
            try {
                sendAll(base, session, deleteAfter)
            } catch (exc: Exception) {
                if (!TransferHub.cancel) {
                    val text = exc.message?.ifBlank { null } ?: getString(R.string.err_generic)
                    TransferHub.state.value = TransferState(error = text)
                    notifyDone(getString(R.string.notif_failed), text)
                }
            } finally {
                if (lock.isHeld) lock.release()
                working = false
                stopSelf()
            }
        }
        return START_NOT_STICKY
    }

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }

    private suspend fun sendAll(base: String, session: String, deleteAfter: Boolean) {
        if (base.isBlank()) throw IllegalStateException(getString(R.string.err_unreachable))
        val cfg = ConfigStore(this).config.first()
        if (isServerTemplate(cfg.server)) throw IllegalStateException(getString(R.string.err_server_template))
        val server = cfg.server.trim().trimEnd('/')
        val ids = if (session == "*") {
            val listed = getText("$base/v1/sessions") ?: throw IllegalStateException(getString(R.string.err_unreachable))
            parseSessions(listed).map { it.id }.filter { sessionOk(it) }
        } else {
            listOf(session).filter { sessionOk(it) }
        }
        if (ids.isEmpty()) {
            TransferHub.state.value = TransferState(note = getString(R.string.no_sessions))
            notifyDone(getString(R.string.notif_done), getString(R.string.no_sessions))
            return
        }
        var done = 0
        var total = 0
        for (id in ids) {
            if (TransferHub.cancel) break
            val files = listOf("session.json", "imu0.csv", "cam0/video.mp4")
            total += files.size
            val meta = getText("$base/v1/sessions/$id/session.json")
            if (meta != null) {
                post("$server/sessions", meta.toRequestBody("application/json".toMediaType()), cfg.token, allowConflict = true)
            }
            for (rel in files) {
                if (TransferHub.cancel) break
                val tmp = download("$base/v1/sessions/$id/$rel") ?: continue
                try {
                    val type = when {
                        rel.endsWith(".mp4") -> "video/mp4"
                        rel.endsWith(".json") -> "application/json"
                        else -> "text/csv"
                    }
                    post(
                        "$server/sessions/$id/files",
                        tmp.asRequestBody(type.toMediaType()),
                        cfg.token,
                        extra = mapOf(
                            "X-CameVision-Path" to rel,
                            "X-CameVision-Session" to id,
                        ),
                    )
                } finally {
                    tmp.delete()
                }
                done += 1
                val note = getString(R.string.transfer_progress, done, total)
                TransferHub.state.value = TransferState(running = true, done = done, total = total, note = note)
                notifyProgress(note, done, total)
            }
            if (!TransferHub.cancel) {
                post(
                    "$server/sessions/$id/complete",
                    """{"id":"$id","product":"CV-EGO01-SS"}""".toRequestBody("application/json".toMediaType()),
                    cfg.token,
                    allowConflict = true,
                )
                postCommand(base, """{"cmd":"mark","session":"$id"}""")
                if (deleteAfter) postCommand(base, """{"cmd":"delete","session":"$id"}""")
            }
        }
        if (TransferHub.cancel) {
            TransferHub.state.value = TransferState(note = getString(R.string.transfer_cancel))
            notifyDone(getString(R.string.notif_failed), getString(R.string.transfer_cancel))
        } else {
            val note = getString(R.string.transfer_done)
            TransferHub.state.value = TransferState(note = note)
            notifyDone(getString(R.string.notif_done), note)
        }
    }

    private fun sessionOk(id: String) = Regex("^[0-9]{8}T[0-9]{6}Z$").matches(id)

    private fun getText(url: String): String? {
        val bytes = getBytes(url) ?: return null
        return bytes.toString(Charsets.UTF_8)
    }

    private fun getBytes(url: String): ByteArray? {
        return try {
            http.newCall(Request.Builder().url(url).header("User-Agent", "CameVision").build()).execute().use { resp ->
                if (!resp.isSuccessful) null else resp.body?.bytes()
            }
        } catch (_: Exception) {
            null
        }
    }

    private fun download(url: String): File? {
        return try {
            http.newCall(Request.Builder().url(url).header("User-Agent", "CameVision").build()).execute().use { resp ->
                if (!resp.isSuccessful) return null
                val file = File.createTempFile("camevision", ".part", cacheDir)
                resp.body?.byteStream()?.use { input ->
                    file.outputStream().use { output -> input.copyTo(output) }
                } ?: return null
                file
            }
        } catch (_: Exception) {
            null
        }
    }

    private fun post(
        url: String,
        body: RequestBody,
        token: String,
        allowConflict: Boolean = false,
        extra: Map<String, String> = emptyMap(),
    ) {
        val builder = Request.Builder().url(url).post(body).header("User-Agent", "CameVision")
            .header("X-CameVision-Product", "CV-EGO01-SS")
        if (token.isNotBlank()) builder.header("Authorization", "Bearer $token")
        extra.forEach { (key, value) -> builder.header(key, value) }
        http.newCall(builder.build()).execute().use { resp ->
            if (resp.isSuccessful) return
            if (allowConflict && resp.code == 409) return
            throw IllegalStateException(getString(R.string.err_upload))
        }
    }

    private fun postCommand(base: String, json: String) {
        try {
            post("$base/v1/cmd", json.toRequestBody("application/json".toMediaType()), "", allowConflict = true)
        } catch (_: Exception) {
        }
    }

    private fun ensureChannel() {
        if (Build.VERSION.SDK_INT < 26) return
        val manager = getSystemService(NotificationManager::class.java)
        val channel = NotificationChannel(CHANNEL, "CameVision", NotificationManager.IMPORTANCE_LOW)
        manager.createNotificationChannel(channel)
    }

    private fun notifyProgress(text: String, done: Int, total: Int) {
        getSystemService(NotificationManager::class.java).notify(NOTIF_ID, note(text, done, total, true))
    }

    private fun notifyDone(title: String, text: String) {
        val built = NotificationCompat.Builder(this, CHANNEL)
            .setSmallIcon(R.drawable.ic_stat)
            .setContentTitle(title)
            .setContentText(text)
            .setContentIntent(openApp())
            .setAutoCancel(true)
            .build()
        stopForeground(STOP_FOREGROUND_DETACH)
        getSystemService(NotificationManager::class.java).notify(NOTIF_ID, built)
    }

    private fun note(text: String, done: Int, total: Int, ongoing: Boolean): Notification {
        return NotificationCompat.Builder(this, CHANNEL)
            .setSmallIcon(R.drawable.ic_stat)
            .setContentTitle(getString(R.string.notif_sending))
            .setContentText(text)
            .setContentIntent(openApp())
            .setOngoing(ongoing)
            .setOnlyAlertOnce(true)
            .setProgress(total.coerceAtLeast(1), done, total == 0)
            .build()
    }

    private fun openApp(): PendingIntent {
        val intent = Intent(this, MainActivity::class.java)
        val flags = PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        return PendingIntent.getActivity(this, 0, intent, flags)
    }

    companion object {
        const val EXTRA_BASE = "base"
        const val EXTRA_SESSION = "session"
        const val EXTRA_DELETE = "delete"
        private const val CHANNEL = "camevision-send"
        private const val NOTIF_ID = 41
    }
}

fun notifyCardFull(context: Context) {
    if (Build.VERSION.SDK_INT >= 33) {
        val granted = context.checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) ==
            android.content.pm.PackageManager.PERMISSION_GRANTED
        if (!granted) return
    }
    val manager = context.getSystemService(NotificationManager::class.java)
    if (Build.VERSION.SDK_INT >= 26) {
        val channel = NotificationChannel("camevision-card", "CameVision", NotificationManager.IMPORTANCE_DEFAULT)
        manager.createNotificationChannel(channel)
    }
    val intent = Intent(context, MainActivity::class.java)
    val flags = PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
    val pending = PendingIntent.getActivity(context, 1, intent, flags)
    val note = NotificationCompat.Builder(context, "camevision-card")
        .setSmallIcon(R.drawable.ic_stat)
        .setContentTitle(context.getString(R.string.card_signal_title))
        .setContentText(context.getString(R.string.card_signal_body))
        .setContentIntent(pending)
        .setAutoCancel(true)
        .build()
    manager.notify(42, note)
}
