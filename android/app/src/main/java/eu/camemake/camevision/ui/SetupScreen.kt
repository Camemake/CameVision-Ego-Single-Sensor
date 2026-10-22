package eu.camemake.camevision.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import eu.camemake.camevision.CameVisionModel
import eu.camemake.camevision.CaptureMode
import eu.camemake.camevision.FoundDevice
import eu.camemake.camevision.LinkState
import eu.camemake.camevision.R
import eu.camemake.camevision.WifiNet
import kotlin.math.roundToInt

@Composable
fun SetupScreen(
    model: CameVisionModel,
    link: LinkState,
    banner: String,
    bluetoothOn: Boolean,
    onPair: () -> Unit,
    onPick: (FoundDevice) -> Unit,
    onForget: () -> Unit,
    onBluetooth: () -> Unit,
) {
    val draft by model.draft.collectAsState()
    val online = draft.mode == CaptureMode.Online
    var showPassword by rememberSaveable { mutableStateOf(false) }
    LaunchedEffect(link.transport) {
        if (link.transport.isNotEmpty()) model.scanWifi()
    }
    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp, vertical = 8.dp),
    ) {
        Text(stringResource(R.string.setup_title), fontWeight = FontWeight.ExtraBold, fontSize = 32.sp, color = CameInk)
        Spacer(Modifier.height(16.dp))
        FieldCard {
            SectionLabel(stringResource(R.string.bt_label))
            if (!bluetoothOn) {
                Text(stringResource(R.string.err_bluetooth), color = CameMuted, fontSize = 14.sp)
                PinkButton(stringResource(R.string.connect_bluetooth), Modifier.fillMaxWidth(), onBluetooth)
            } else if (link.transport == "ble") {
                Text(link.name.ifBlank { stringResource(R.string.product_title) }, fontWeight = FontWeight.SemiBold, color = CameInk)
                if (link.paired) {
                    Text(stringResource(R.string.bt_paired), color = CameTeal, fontSize = 13.sp)
                }
                QuietButton(stringResource(R.string.bt_forget), Modifier.fillMaxWidth(), onForget)
            } else {
                Text(stringResource(R.string.not_connected), color = CameMuted, fontSize = 14.sp)
                PinkButton(stringResource(R.string.bt_pair), Modifier.fillMaxWidth(), onPair)
            }
            if (link.scanning || link.found.isNotEmpty()) {
                if (link.found.isEmpty()) {
                    Text(stringResource(R.string.connect_scanning), color = CameMuted, fontSize = 14.sp)
                }
                link.found.forEach { device ->
                    Row(
                        Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(12.dp))
                            .clickable { onPick(device) }
                            .padding(vertical = 8.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Column(Modifier.weight(1f)) {
                            Text(device.name, fontWeight = FontWeight.SemiBold, color = CameInk)
                            Text(device.address, color = CameMuted, fontSize = 12.sp)
                        }
                        SignalBars(device.rssi)
                    }
                }
                if (link.transport != "ble") {
                    QuietButton(stringResource(R.string.connect_again), Modifier.fillMaxWidth(), onPair)
                }
            }
        }
        Spacer(Modifier.height(12.dp))
        FieldCard {
            SectionLabel(stringResource(R.string.mode_label))
            ModeSwitch(online = online, enabled = !link.status.recording) { wantServer ->
                model.setMode(if (wantServer) CaptureMode.Online else CaptureMode.Standalone)
            }
        }
        Spacer(Modifier.height(12.dp))
        FieldCard {
            SectionLabel(stringResource(R.string.server_label))
            OutlinedTextField(
                value = draft.server,
                onValueChange = { model.updateDraft(model.draft.value.copy(server = it)) },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri),
            )
            Text(stringResource(R.string.token_label), fontWeight = FontWeight.SemiBold, fontSize = 14.sp, color = CameInk)
            Help(stringResource(R.string.token_hint))
            OutlinedTextField(
                value = draft.token,
                onValueChange = { model.updateDraft(model.draft.value.copy(token = it)) },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                visualTransformation = PasswordVisualTransformation(),
            )
        }
        Spacer(Modifier.height(12.dp))
        FieldCard {
            SectionLabel(stringResource(R.string.wifi_label))
            if (link.transport.isNotEmpty()) {
                val wifiText = when (link.status.wifi) {
                    "up" -> stringResource(R.string.wifi_up)
                    "joining" -> stringResource(R.string.wifi_joining)
                    else -> stringResource(R.string.wifi_down)
                }
                val joined = link.status.ssid
                Text(
                    if (joined.isBlank()) wifiText else "$wifiText · $joined",
                    color = CameInk,
                    fontSize = 14.sp,
                )
            }
            if (link.transport.isNotEmpty() && link.networks.isEmpty()) {
                Text(stringResource(R.string.wifi_empty), color = CameMuted, fontSize = 14.sp)
            }
            link.networks.forEach { net ->
                WifiRow(net, selected = net.ssid == draft.ssid) {
                    model.updateDraft(model.draft.value.copy(ssid = net.ssid))
                }
            }
            if (link.transport.isNotEmpty()) {
                QuietButton(stringResource(R.string.wifi_scan), Modifier.fillMaxWidth()) { model.scanWifi() }
            }
            OutlinedTextField(
                value = draft.ssid,
                onValueChange = { model.updateDraft(model.draft.value.copy(ssid = it)) },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                label = { Text(stringResource(R.string.ssid_label)) },
            )
            OutlinedTextField(
                value = draft.psk,
                onValueChange = { model.updateDraft(model.draft.value.copy(psk = it)) },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                label = { Text(stringResource(R.string.psk_label)) },
                visualTransformation = if (showPassword) VisualTransformation.None else PasswordVisualTransformation(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                trailingIcon = {
                    IconButton(onClick = { showPassword = !showPassword }) {
                        Icon(
                            if (showPassword) Icons.Filled.VisibilityOff else Icons.Filled.Visibility,
                            contentDescription = null,
                        )
                    }
                },
            )
        }
        Spacer(Modifier.height(12.dp))
        FieldCard {
            SectionLabel(stringResource(R.string.warn_label))
            Text(stringResource(R.string.warn_value, draft.warn), color = CameMuted, fontSize = 14.sp)
            Slider(
                value = draft.warn.toFloat(),
                onValueChange = { model.updateDraft(model.draft.value.copy(warn = it.roundToInt())) },
                valueRange = 70f..95f,
                steps = 24,
            )
        }
        Spacer(Modifier.height(12.dp))
        FieldCard {
            SectionLabel(stringResource(R.string.host_label))
            OutlinedTextField(
                value = draft.host,
                onValueChange = { model.updateDraft(model.draft.value.copy(host = it)) },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri),
            )
        }
        Spacer(Modifier.height(16.dp))
        PinkButton(stringResource(R.string.save), Modifier.fillMaxWidth()) { model.save() }
        val shown = bannerText(banner)
        if (shown != null) {
            Spacer(Modifier.height(10.dp))
            Text(shown.first, color = if (shown.second) CameTeal else CamePink, fontSize = 14.sp)
        }
        Spacer(Modifier.height(18.dp))
        FieldCard {
            SectionLabel(stringResource(R.string.about))
            Text(stringResource(R.string.about_product), fontWeight = FontWeight.SemiBold, color = CameInk)
            Text(stringResource(R.string.about_sku), color = CameMuted, fontSize = 14.sp)
        }
        Spacer(Modifier.height(20.dp))
    }
}

@Composable
private fun WifiRow(net: WifiNet, selected: Boolean, onClick: () -> Unit) {
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(if (selected) Color(0xFFE7F2F4) else Color.Transparent)
            .clickable(onClick = onClick)
            .padding(horizontal = 8.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(net.ssid, modifier = Modifier.weight(1f), color = CameInk, fontWeight = FontWeight.Medium)
        Spacer(Modifier.width(8.dp))
        SignalBars(net.rssi)
    }
}

@Composable
private fun SignalBars(rssi: Int) {
    val level = when {
        rssi >= -55 -> 4
        rssi >= -67 -> 3
        rssi >= -75 -> 2
        rssi >= -85 -> 1
        else -> 0
    }
    Row(
        horizontalArrangement = Arrangement.spacedBy(2.dp),
        verticalAlignment = Alignment.Bottom,
    ) {
        for (bar in 1..4) {
            Box(
                Modifier
                    .size(width = 4.dp, height = (4 + bar * 4).dp)
                    .clip(RoundedCornerShape(1.dp))
                    .background(if (bar <= level) CameTeal else CameLine),
            )
        }
    }
}
