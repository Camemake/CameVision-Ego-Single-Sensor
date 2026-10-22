package eu.camemake.camevision

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.camevisionStore by preferencesDataStore(name = "camevision")

class ConfigStore(private val context: Context) {
    private val server = stringPreferencesKey("server")
    private val token = stringPreferencesKey("token")
    private val ssid = stringPreferencesKey("ssid")
    private val psk = stringPreferencesKey("psk")
    private val warn = intPreferencesKey("warn")
    private val mode = stringPreferencesKey("mode")
    private val host = stringPreferencesKey("host")
    private val address = stringPreferencesKey("address")

    val config: Flow<AppConfig> = context.camevisionStore.data.map { prefs ->
        AppConfig(
            server = prefs[server] ?: SERVER_TEMPLATE,
            token = prefs[token] ?: "",
            ssid = prefs[ssid] ?: "",
            psk = prefs[psk] ?: "",
            warn = prefs[warn] ?: 85,
            mode = modeOf(prefs[mode]),
            host = prefs[host] ?: "",
            address = prefs[address] ?: "",
        )
    }

    suspend fun save(cfg: AppConfig) {
        context.camevisionStore.edit { prefs ->
            prefs[server] = cfg.server.trim()
            prefs[token] = cfg.token
            prefs[ssid] = cfg.ssid.trim()
            prefs[psk] = cfg.psk
            prefs[warn] = cfg.warn.coerceIn(70, 95)
            prefs[mode] = cfg.mode.wire()
            prefs[host] = cfg.host.trim()
            prefs[address] = cfg.address
        }
    }

    suspend fun setMode(value: CaptureMode) {
        context.camevisionStore.edit { prefs -> prefs[mode] = value.wire() }
    }

    suspend fun setAddress(value: String) {
        context.camevisionStore.edit { prefs -> prefs[address] = value }
    }
}
