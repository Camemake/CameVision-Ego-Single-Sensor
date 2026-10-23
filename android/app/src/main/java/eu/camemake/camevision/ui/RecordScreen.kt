package eu.camemake.camevision.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import eu.camemake.camevision.CameVisionModel
import eu.camemake.camevision.CaptureMode
import eu.camemake.camevision.LinkState
import eu.camemake.camevision.R
import eu.camemake.camevision.TransferState
import eu.camemake.camevision.frontTitle
import kotlinx.coroutines.delay

@Composable
fun RecordScreen(
    model: CameVisionModel,
    link: LinkState,
    transfer: TransferState,
    banner: String,
    onConnect: () -> Unit,
    onSend: () -> Unit,
) {
    val status = link.status
    val draft by model.draft.collectAsState()
    val started by model.recordStarted.collectAsState()
    val online = draft.mode == CaptureMode.Online
    var now by remember { mutableLongStateOf(System.currentTimeMillis()) }
    if (status.recording) {
        LaunchedEffect(started) {
            while (true) {
                now = System.currentTimeMillis()
                delay(500)
            }
        }
    }
    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp, vertical = 8.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            frontTitle(link.transport == "ble", status, link.name),
            color = CameInk,
            fontWeight = FontWeight.ExtraBold,
            fontSize = 26.sp,
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(22.dp))
        RecordButton(recording = status.recording) {
            model.toggleRecord()
        }
        Spacer(Modifier.height(12.dp))
        Text(
            if (status.recording) stringResource(R.string.recording) else stringResource(R.string.start_recording),
            fontWeight = FontWeight.Bold,
            fontSize = 18.sp,
            color = CameInk,
        )
        if (status.recording) {
            Text(
                stringResource(R.string.stop_recording),
                fontWeight = FontWeight.SemiBold,
                fontSize = 15.sp,
                color = CameMuted,
            )
        }
        if (status.recording) {
            val elapsed = formatElapsed(now - started)
            val size = if (status.width > 0 && status.height > 0) {
                stringResource(R.string.resolution, status.width, status.height)
            } else {
                stringResource(R.string.full_video)
            }
            Text(
                stringResource(R.string.stat_line, elapsed, size, status.imuHz.toInt()),
                color = CameMuted,
                fontSize = 14.sp,
            )
        }
        Spacer(Modifier.height(18.dp))
        StoragePanel(status)
        if (status.sdWarn) {
            Spacer(Modifier.height(10.dp))
            WarnBanner()
        }
        if (online && link.transport.isNotEmpty()) {
            Spacer(Modifier.height(10.dp))
            OnlineLine(status.wifi, status.ssid, status.pending, status.sent)
        }
        val shown = bannerText(banner.ifBlank { status.error })
        if (shown != null) {
            Spacer(Modifier.height(10.dp))
            Text(
                shown.first,
                color = if (shown.second) CameTeal else CamePink,
                fontSize = 14.sp,
                lineHeight = 20.sp,
                modifier = Modifier.fillMaxWidth(),
            )
        }
        if (transfer.running || transfer.note.isNotBlank() || transfer.error.isNotBlank()) {
            Spacer(Modifier.height(10.dp))
            TransferLine(transfer, model)
        }
        Spacer(Modifier.height(16.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            QuietButton(stringResource(R.string.preview), Modifier.weight(1f)) { model.startPreview() }
            QuietButton(stringResource(R.string.qr_trigger), Modifier.weight(1f)) { model.openQr() }
        }
        Spacer(Modifier.height(10.dp))
        val sendLabel = stringResource(if (online) R.string.send_leftovers else R.string.send)
        if (status.sdWarn && !online) {
            PinkButton(sendLabel, Modifier.fillMaxWidth(), onSend)
        } else {
            QuietButton(sendLabel, Modifier.fillMaxWidth(), onSend)
        }
        Spacer(Modifier.height(12.dp))
    }
}

@Composable
private fun OnlineLine(wifi: String, ssid: String, pending: Int, sent: Int) {
    val wifiText = when (wifi) {
        "up" -> stringResource(R.string.wifi_up)
        "joining" -> stringResource(R.string.wifi_joining)
        else -> stringResource(R.string.wifi_down)
    }
    Column(
        Modifier
            .fillMaxWidth()
            .clipCard()
            .padding(14.dp),
    ) {
        Text(if (ssid.isBlank()) wifiText else "$wifiText · $ssid", fontWeight = FontWeight.SemiBold, color = CameInk)
        Spacer(Modifier.height(4.dp))
        Text(stringResource(R.string.upload_line, pending, sent), color = CameMuted, fontSize = 14.sp)
    }
}

@Composable
private fun TransferLine(transfer: TransferState, model: CameVisionModel) {
    Column(Modifier.fillMaxWidth().clipCard().padding(14.dp)) {
        val title = when {
            transfer.error.isNotBlank() -> transfer.error
            transfer.note.isNotBlank() -> transfer.note
            else -> stringResource(R.string.transfer_title)
        }
        Text(title, color = if (transfer.error.isNotBlank()) CamePink else CameInk, fontSize = 14.sp)
        if (transfer.running) {
            Spacer(Modifier.height(8.dp))
            Text(
                stringResource(R.string.transfer_cancel),
                color = CameTeal,
                fontWeight = FontWeight.SemiBold,
                modifier = Modifier.clickable { model.cancelSend() },
            )
        }
    }
}

private fun Modifier.clipCard(): Modifier = this
    .clip(RoundedCornerShape(16.dp))
    .background(Color.White)
    .border(1.dp, CameLine, RoundedCornerShape(16.dp))
