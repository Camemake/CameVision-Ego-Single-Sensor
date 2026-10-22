package eu.camemake.camevision

import android.Manifest
import android.app.Application
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.content.ContextCompat
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import org.json.JSONObject

class CameVisionModel(app: Application) : AndroidViewModel(app) {
    private val store = ConfigStore(app)
    val link = Link(app)
    val draft = MutableStateFlow(AppConfig())
    val saved = MutableStateFlow(AppConfig())
    val banner = MutableStateFlow("")
    val previewImage = MutableStateFlow<ByteArray?>(null)
    val previewUntil = MutableStateFlow(0L)
    val recordStarted = MutableStateFlow(0L)

    private var draftReady = false
    private var warned = false

    init {
        link.onFrame = { jpg -> previewImage.value = jpg }
        link.onReady = {
            viewModelScope.launch {
                val cfg = store.config.first()
                link.command(configJson(cfg))
                link.command("""{"cmd":"list"}""")
            }
        }
        viewModelScope.launch {
            store.config.collect { cfg ->
                saved.value = cfg
                if (!draftReady) {
                    draftReady = true
                    draft.value = cfg
                }
                link.watchHttp(cfg.host)
            }
        }
        viewModelScope.launch {
            val cfg = store.config.first()
            if (cfg.address.isNotBlank() && btGranted()) {
                link.connect(cfg.address)
            }
        }
        viewModelScope.launch {
            var wasRecording = false
            link.state.collect { state ->
                val recording = state.status.recording
                if (recording && !wasRecording) recordStarted.value = System.currentTimeMillis()
                if (!recording) recordStarted.value = 0L
                wasRecording = recording
                if (state.status.sdWarn && !warned && state.transport.isNotEmpty()) {
                    warned = true
                    notifyCardFull(getApplication())
                }
                if (!state.status.sdWarn) warned = false
            }
        }
        viewModelScope.launch {
            while (isActive) {
                delay(4000)
                if (link.state.value.transport == "ble") link.command("""{"cmd":"list"}""")
            }
        }
    }

    fun updateDraft(cfg: AppConfig) {
        draft.value = cfg
    }

    fun findCamera() {
        banner.value = ""
        if (!link.bluetoothOn()) {
            banner.value = "bluetooth"
            return
        }
        if (btGranted()) link.scan()
    }

    fun choose(device: FoundDevice) {
        viewModelScope.launch { store.setAddress(device.address) }
        link.connect(device.address, device.name)
    }

    fun forget() {
        link.disconnect()
        viewModelScope.launch { store.setAddress("") }
    }

    fun scanWifi() {
        if (link.state.value.transport.isEmpty()) return
        link.command("""{"cmd":"wifi"}""")
    }

    fun setMode(mode: CaptureMode) {
        if (link.state.value.status.recording) return
        draft.value = draft.value.copy(mode = mode)
        viewModelScope.launch { store.setMode(mode) }
        if (link.state.value.transport.isNotEmpty()) {
            link.command("""{"cmd":"mode","mode":"${mode.wire()}"}""")
        }
    }

    fun toggleRecord() {
        banner.value = ""
        val state = link.state.value
        if (state.transport.isEmpty() && saved.value.host.isBlank()) {
            findCamera()
            return
        }
        if (state.status.recording) {
            link.command("""{"cmd":"stop"}""")
        } else {
            val mode = draft.value.mode.wire()
            link.command("""{"cmd":"start","mode":"$mode"}""")
        }
    }

    fun startPreview() {
        banner.value = ""
        previewImage.value = null
        val until = System.currentTimeMillis() + 4_000
        previewUntil.value = until
        link.command("""{"cmd":"preview","seconds":4}""")
    }

    fun stopPreview() {
        previewUntil.value = 0L
        link.command("""{"cmd":"preview","seconds":0}""")
    }

    fun save() {
        val cfg = draft.value
        viewModelScope.launch {
            store.save(cfg)
            val linked = link.state.value.transport.isNotEmpty()
            if (linked) {
                link.command(configJson(cfg))
                banner.value = "saved_sent"
            } else {
                banner.value = "saved"
            }
        }
    }

    fun clearCard() {
        banner.value = ""
        link.command("""{"cmd":"clear"}""")
    }

    fun deleteSession(id: String) {
        banner.value = ""
        link.command("""{"cmd":"delete","session":"$id"}""")
    }

    fun send(session: String, deleteAfter: Boolean) {
        val cfg = saved.value
        if (isServerTemplate(cfg.server)) {
            banner.value = "server_template"
            return
        }
        val base = cameraBase(link.state.value.status.ip, cfg.host)
        if (base.isBlank()) {
            banner.value = "unreachable"
            return
        }
        banner.value = ""
        val intent = Intent(getApplication(), SendService::class.java)
            .putExtra(SendService.EXTRA_BASE, base)
            .putExtra(SendService.EXTRA_SESSION, session)
            .putExtra(SendService.EXTRA_DELETE, deleteAfter)
        ContextCompat.startForegroundService(getApplication(), intent)
    }

    fun cancelSend() {
        TransferHub.cancel = true
    }

    fun btGranted(): Boolean {
        return btPermissions().all { permission ->
            ContextCompat.checkSelfPermission(getApplication(), permission) == PackageManager.PERMISSION_GRANTED
        }
    }

    fun btPermissions(): Array<String> {
        return if (Build.VERSION.SDK_INT >= 31) {
            arrayOf(Manifest.permission.BLUETOOTH_SCAN, Manifest.permission.BLUETOOTH_CONNECT)
        } else {
            arrayOf(Manifest.permission.ACCESS_FINE_LOCATION)
        }
    }

    fun notifPermission(): String? {
        return if (Build.VERSION.SDK_INT >= 33) Manifest.permission.POST_NOTIFICATIONS else null
    }

    override fun onCleared() {
        link.close()
        super.onCleared()
    }

    private fun configJson(cfg: AppConfig): String {
        val obj = JSONObject()
        obj.put("cmd", "config")
        obj.put("server", cfg.server.trim())
        obj.put("token", cfg.token)
        obj.put("warn", cfg.warn)
        obj.put("mode", cfg.mode.wire())
        if (cfg.ssid.isNotBlank()) {
            obj.put("ssid", cfg.ssid.trim())
            obj.put("psk", cfg.psk)
        }
        return obj.toString()
    }
}
