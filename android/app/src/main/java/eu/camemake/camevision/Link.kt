package eu.camemake.camevision

import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCallback
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothGattDescriptor
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothProfile
import android.bluetooth.BluetoothStatusCodes
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.Context
import android.os.Build
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.TimeUnit

class Link(context: Context) {
    private val app = context.applicationContext
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val http = OkHttpClient.Builder()
        .connectTimeout(8, TimeUnit.SECONDS)
        .readTimeout(20, TimeUnit.SECONDS)
        .writeTimeout(20, TimeUnit.SECONDS)
        .build()
    private val jsonType = "application/json; charset=utf-8".toMediaType()
    private val adapter: BluetoothAdapter? =
        app.getSystemService(BluetoothManager::class.java)?.adapter

    val state = kotlinx.coroutines.flow.MutableStateFlow(LinkState())
    var onReady: () -> Unit = {}
    var onFrame: (ByteArray) -> Unit = {}

    private val infoAsm = InfoAssembler()
    private val frameAsm = FrameAssembler()
    private val found = ConcurrentHashMap<String, FoundDevice>()
    private var gatt: BluetoothGatt? = null
    private var commandChar: BluetoothGattCharacteristic? = null
    private var infoReady = false
    private var frameReady = false
    private var bleReady = false
    private val writes = ArrayDeque<ByteArray>()
    private var writing = false
    private var httpJob: Job? = null
    private var httpHost = ""
    private var attMtu = 23

    fun bluetoothOn(): Boolean = adapter?.isEnabled == true

    @SuppressLint("MissingPermission")
    fun scan() {
        val scanner = adapter?.bluetoothLeScanner
        if (scanner == null || adapter?.isEnabled != true) {
            patch { it.copy(scanning = false) }
            return
        }
        found.clear()
        patch { it.copy(scanning = true, found = emptyList()) }
        val settings = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            .apply {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    setLegacy(false)
                    setPhy(ScanSettings.PHY_LE_ALL_SUPPORTED)
                }
            }
            .build()
        try {
            scanner.stopScan(scanCallback)
        } catch (_: Exception) {
        }
        try {
            scanner.startScan(null, settings, scanCallback)
        } catch (_: SecurityException) {
            patch { it.copy(scanning = false) }
            return
        } catch (_: IllegalArgumentException) {
            val fallback = ScanSettings.Builder()
                .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
                .build()
            scanner.startScan(null, fallback, scanCallback)
        }
        scope.launch {
            delay(12_000)
            stopScan()
        }
    }

    @SuppressLint("MissingPermission")
    fun stopScan() {
        try {
            adapter?.bluetoothLeScanner?.stopScan(scanCallback)
        } catch (_: Exception) {
        }
        patch { it.copy(scanning = false) }
    }

    @SuppressLint("MissingPermission")
    fun connect(address: String, name: String = "") {
        val device = try {
            adapter?.getRemoteDevice(address)
        } catch (_: IllegalArgumentException) {
            null
        } ?: return
        stopScan()
        closeGatt()
        bleReady = false
        infoReady = false
        frameReady = false
        patch { it.copy(transport = "", name = name.ifBlank { it.name }, paired = false) }
        try {
            gatt = device.connectGatt(app, false, gattCallback, BluetoothDevice.TRANSPORT_LE)
        } catch (_: SecurityException) {
            patch { it.copy(transport = "") }
        }
    }

    fun disconnect() {
        closeGatt()
        if (httpHost.isBlank()) {
            patch { it.copy(transport = "", name = "") }
        } else {
            patch { it.copy(transport = if (state.value.transport == "ble") "http" else it.transport) }
        }
    }

    fun watchHttp(host: String) {
        httpHost = host.trim()
        httpJob?.cancel()
        if (httpHost.isBlank()) {
            if (state.value.transport == "http") {
                patch { it.copy(transport = "") }
            }
            return
        }
        httpJob = scope.launch {
            while (isActive) {
                val base = cameraBase(state.value.status.ip, httpHost)
                if (base.isNotBlank()) {
                    val body = get(base + "/v1/status")
                    if (body != null) {
                        val event = parseInfo(body)
                        if (event is InfoEvent.Status) {
                            patch {
                                it.copy(
                                    transport = if (bleReady) "ble" else "http",
                                    name = it.name.ifBlank { "CameVision" },
                                    status = event.status,
                                )
                            }
                        }
                        val sessions = get(base + "/v1/sessions")
                        if (sessions != null) {
                            patch { it.copy(sessions = parseSessions(sessions)) }
                        }
                    } else if (!bleReady && state.value.transport == "http") {
                        patch { it.copy(transport = "") }
                    }
                }
                delay(1000)
            }
        }
    }

    fun setRecording(on: Boolean) {
        patch { it.copy(status = it.status.copy(recording = on, error = if (on) "" else it.status.error)) }
    }

    fun command(json: String, httpToo: Boolean = false) {
        if (bleReady) {
            enqueue(blePayload(json))
        } else if (!httpToo) {
            patch { it.copy(status = it.status.copy(error = "pair")) }
            return
        }
        if (httpToo) {
            val base = cameraBase(state.value.status.ip, httpHost)
            if (base.isNotBlank()) {
                scope.launch { applyHttpCommand(base, json) }
            }
        }
    }

    suspend fun getBytes(url: String): ByteArray? = withContext(Dispatchers.IO) {
        try {
            http.newCall(Request.Builder().url(url).build()).execute().use { resp ->
                if (!resp.isSuccessful) null else resp.body?.bytes()
            }
        } catch (_: Exception) {
            null
        }
    }

    fun close() {
        httpJob?.cancel()
        stopScan()
        closeGatt()
        scope.coroutineContext[Job]?.cancel()
    }

    private fun applyHttpCommand(base: String, json: String) {
        applyInfo(post(base, json))
        applyInfo(get("$base/v1/status"))
        if (json.contains("\"wifi\"") && state.value.networks.isEmpty()) {
            applyInfo(get("$base/v1/wifi"))
        }
        if (
            json.contains("\"list\"") ||
            json.contains("\"start\"") ||
            json.contains("\"stop\"") ||
            json.contains("\"clear\"") ||
            json.contains("\"delete\"")
        ) {
            val sessions = get("$base/v1/sessions")
            if (sessions != null) {
                patch { it.copy(sessions = parseSessions(sessions)) }
            }
        }
    }

    private fun applyInfo(body: String?) {
        if (body.isNullOrBlank()) return
        when (val event = parseInfo(body)) {
            is InfoEvent.Status -> patch {
                it.copy(
                    transport = if (bleReady) "ble" else "http",
                    name = it.name.ifBlank { "CameVision" },
                    status = event.status,
                )
            }
            is InfoEvent.Sessions -> patch { it.copy(sessions = event.items) }
            is InfoEvent.Wifi -> patch { it.copy(networks = event.items) }
            is InfoEvent.Hello -> patch { it.copy(name = event.name.ifBlank { it.name }) }
            is InfoEvent.Ack -> {
                if (!event.ok && event.error.isNotBlank()) {
                    patch { it.copy(status = it.status.copy(error = event.error)) }
                }
            }
            null -> {
                try {
                    val obj = JSONObject(body)
                    if (obj.has("ok") && !obj.optBoolean("ok")) {
                        val err = obj.optString("error")
                        if (err.isNotBlank()) {
                            patch { it.copy(status = it.status.copy(error = err)) }
                        }
                    }
                } catch (_: Exception) {
                }
            }
        }
    }

    private fun post(base: String, json: String): String? {
        return try {
            val body = json.toRequestBody(jsonType)
            val request = Request.Builder().url("$base/v1/cmd").post(body).build()
            http.newCall(request).execute().use { resp ->
                if (!resp.isSuccessful) null else resp.body?.string()
            }
        } catch (_: Exception) {
            null
        }
    }

    private fun get(url: String): String? {
        return try {
            http.newCall(Request.Builder().url(url).build()).execute().use { resp ->
                if (!resp.isSuccessful) null else resp.body?.string()
            }
        } catch (_: Exception) {
            null
        }
    }

    private val scanCallback = object : ScanCallback() {
        @SuppressLint("MissingPermission")
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            val record = result.scanRecord
            val name = record?.deviceName ?: result.device.name.orEmpty()
            val uuids = record?.serviceUuids?.map { it.uuid }.orEmpty()
            val cameMac = result.device.address.startsWith("60:48:9C", ignoreCase = true)
            if (!name.contains("CameVision", ignoreCase = true) && Protocol.service !in uuids && !cameMac) return
            val shown = name.ifBlank { "CameVision" }
            val device = FoundDevice(shown, result.device.address, result.rssi)
            found[device.address] = device
            patch { it.copy(found = found.values.sortedByDescending { item -> item.rssi }) }
        }
    }

    private val gattCallback = object : BluetoothGattCallback() {
        @SuppressLint("MissingPermission")
        override fun onConnectionStateChange(gatt: BluetoothGatt, status: Int, newState: Int) {
            if (newState == BluetoothProfile.STATE_CONNECTED && status == BluetoothGatt.GATT_SUCCESS) {
                gatt.requestConnectionPriority(BluetoothGatt.CONNECTION_PRIORITY_HIGH)
                if (!gatt.requestMtu(517)) {
                    gatt.discoverServices()
                } else {
                    scope.launch {
                        delay(900)
                        if (!bleReady) {
                            try {
                                gatt.discoverServices()
                            } catch (_: Exception) {
                            }
                        }
                    }
                }
            } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                bleReady = false
                patch {
                    val transport = if (httpHost.isNotBlank() && it.transport == "http") "http" else ""
                    it.copy(transport = transport)
                }
            }
        }

        @SuppressLint("MissingPermission")
        override fun onMtuChanged(gatt: BluetoothGatt, mtu: Int, status: Int) {
            if (status == BluetoothGatt.GATT_SUCCESS && mtu >= 23) {
                attMtu = mtu
            }
            gatt.discoverServices()
        }

        @SuppressLint("MissingPermission")
        override fun onServicesDiscovered(gatt: BluetoothGatt, status: Int) {
            val service = gatt.getService(Protocol.service) ?: return
            commandChar = service.getCharacteristic(Protocol.command)
            val info = service.getCharacteristic(Protocol.info) ?: return
            enableNotify(gatt, info)
        }

        @SuppressLint("MissingPermission")
        override fun onDescriptorWrite(gatt: BluetoothGatt, descriptor: BluetoothGattDescriptor, status: Int) {
            val service = gatt.getService(Protocol.service)
            val frame = service?.getCharacteristic(Protocol.frame)
            if (!infoReady) {
                infoReady = true
                if (frame != null) {
                    enableNotify(gatt, frame)
                    return
                }
            }
            frameReady = true
            bleReady = true
            val remote = gatt.device
            val name = remote.name ?: "CameVision"
            val paired = remote.bondState == BluetoothDevice.BOND_BONDED
            patch { it.copy(transport = "ble", name = name, paired = paired) }
            enqueue(blePayload("""{"cmd":"hello"}"""))
            onReady()
        }

        override fun onCharacteristicChanged(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
            value: ByteArray,
        ) {
            onValue(characteristic, value)
        }

        @Deprecated("Used before API 33")
        override fun onCharacteristicChanged(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
        ) {
            onValue(characteristic, characteristic.value ?: return)
        }

        override fun onCharacteristicWrite(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
            status: Int,
        ) {
            writing = false
            pumpWrite()
        }
    }

    @SuppressLint("MissingPermission")
    private fun enableNotify(gatt: BluetoothGatt, characteristic: BluetoothGattCharacteristic) {
        gatt.setCharacteristicNotification(characteristic, true)
        val descriptor = characteristic.getDescriptor(Protocol.cccd) ?: return
        val value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
        if (Build.VERSION.SDK_INT >= 33) {
            gatt.writeDescriptor(descriptor, value)
        } else {
            descriptor.value = value
            gatt.writeDescriptor(descriptor)
        }
    }

    private fun onValue(characteristic: BluetoothGattCharacteristic, value: ByteArray) {
        when (characteristic.uuid) {
            Protocol.info -> {
                val text = infoAsm.push(value) ?: return
                when (val event = parseInfo(text)) {
                    is InfoEvent.Status -> patch { it.copy(status = event.status, transport = "ble") }
                    is InfoEvent.Sessions -> patch { it.copy(sessions = event.items) }
                    is InfoEvent.Wifi -> patch { it.copy(networks = event.items) }
                    is InfoEvent.Hello -> patch { it.copy(name = event.name, transport = "ble") }
                    is InfoEvent.Ack -> {
                        patch { state ->
                            var status = state.status
                            if (event.cmd == "start" && event.ok) {
                                status = status.copy(
                                    recording = true,
                                    error = "",
                                    session = event.session.ifBlank { status.session },
                                )
                            } else if (event.cmd == "stop" && event.ok) {
                                status = status.copy(recording = false, error = "")
                            } else if (!event.ok && event.error.isNotBlank()) {
                                status = status.copy(
                                    error = event.error,
                                    recording = if (event.cmd == "start") false else status.recording,
                                )
                            }
                            state.copy(status = status, transport = "ble")
                        }
                    }
                    null -> Unit
                }
            }
            Protocol.frame -> {
                val jpg = frameAsm.push(value) ?: return
                if (jpg.size > 100 && jpg[0] == 0xFF.toByte() && jpg[1] == 0xD8.toByte()
                    && jpg[jpg.size - 2] == 0xFF.toByte() && jpg[jpg.size - 1] == 0xD9.toByte()
                ) {
                    onFrame(jpg)
                }
            }
        }
    }

    @SuppressLint("MissingPermission")
    private fun enqueue(bytes: ByteArray) {
        synchronized(writes) { writes.add(bytes) }
        pumpWrite()
    }

    @SuppressLint("MissingPermission")
    private fun writeCmd(
        gatt: BluetoothGatt,
        characteristic: BluetoothGattCharacteristic,
        next: ByteArray,
        writeType: Int,
    ): Boolean {
        return if (Build.VERSION.SDK_INT >= 33) {
            gatt.writeCharacteristic(characteristic, next, writeType) == BluetoothStatusCodes.SUCCESS
        } else {
            characteristic.writeType = writeType
            characteristic.value = next
            gatt.writeCharacteristic(characteristic)
        }
    }

    @SuppressLint("MissingPermission")
    private fun pumpWrite() {
        val gatt = gatt ?: return
        val characteristic = commandChar ?: return
        val next: ByteArray
        synchronized(writes) {
            if (writing) return
            next = writes.removeFirstOrNull() ?: return
            writing = true
        }
        val ok = writeCmd(gatt, characteristic, next, BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT)
        if (ok) {
            return
        }
        val silent = writeCmd(gatt, characteristic, next, BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE)
        if (silent) {
            writing = false
            scope.launch {
                delay(40)
                pumpWrite()
            }
            return
        }
        synchronized(writes) { writes.add(0, next) }
        writing = false
        scope.launch {
            delay(80)
            pumpWrite()
        }
    }

    private fun blePayload(json: String): ByteArray {
        return try {
            val obj = JSONObject(json)
            if (attMtu >= 23) obj.put("mtu", attMtu)
            obj.toString().toByteArray(Charsets.UTF_8)
        } catch (_: Exception) {
            json.toByteArray(Charsets.UTF_8)
        }
    }

    @SuppressLint("MissingPermission")
    private fun closeGatt() {
        bleReady = false
        writing = false
        attMtu = 23
        synchronized(writes) { writes.clear() }
        try {
            gatt?.disconnect()
            gatt?.close()
        } catch (_: Exception) {
        }
        gatt = null
        commandChar = null
    }

    private fun patch(block: (LinkState) -> LinkState) {
        state.value = block(state.value)
    }
}
