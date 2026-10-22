package eu.camemake.camevision.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import eu.camemake.camevision.CameraStatus
import eu.camemake.camevision.R
import java.text.SimpleDateFormat
import java.util.Locale
import java.util.TimeZone

fun formatBytes(n: Long): String {
    if (n < 0) return "0 B"
    val units = arrayOf("B", "KB", "MB", "GB", "TB")
    var value = n.toDouble()
    var index = 0
    while (value >= 1024 && index < units.lastIndex) {
        value /= 1024
        index += 1
    }
    return if (index == 0) {
        "${n.toInt()} ${units[index]}"
    } else {
        String.format(Locale.getDefault(), "%.1f %s", value, units[index])
    }
}

fun formatElapsed(ms: Long): String {
    val total = (ms / 1000).coerceAtLeast(0)
    val hours = total / 3600
    val minutes = (total % 3600) / 60
    val seconds = total % 60
    return if (hours > 0) {
        "%d:%02d:%02d".format(hours, minutes, seconds)
    } else {
        "%d:%02d".format(minutes, seconds)
    }
}

fun formatSession(id: String): String {
    return try {
        val parser = SimpleDateFormat("yyyyMMdd'T'HHmmss'Z'", Locale.US)
        parser.timeZone = TimeZone.getTimeZone("UTC")
        val date = parser.parse(id) ?: return id
        val out = SimpleDateFormat("d MMM yyyy · HH:mm", Locale.getDefault())
        out.timeZone = TimeZone.getDefault()
        out.format(date)
    } catch (_: Exception) {
        id
    }
}

@Composable
fun bannerText(code: String): Pair<String, Boolean>? {
    if (code.isBlank()) return null
    val calm = code == "saved" || code == "saved_sent"
    val text = when (code) {
        "saved" -> stringResource(R.string.saved)
        "saved_sent" -> stringResource(R.string.saved_sent)
        "no_card" -> stringResource(R.string.err_no_card)
        "no_image" -> stringResource(R.string.err_no_image)
        "card_full" -> stringResource(R.string.err_card_full)
        "recording" -> stringResource(R.string.err_recording)
        "server_template" -> stringResource(R.string.err_server_template)
        "upload_failed" -> stringResource(R.string.err_upload)
        "bad_session" -> stringResource(R.string.err_session)
        "unreachable" -> stringResource(R.string.err_unreachable)
        "wifi" -> stringResource(R.string.err_wifi)
        "bluetooth" -> stringResource(R.string.err_bluetooth)
        "permission" -> stringResource(R.string.connect_permission)
        else -> code
    }
    return text to calm
}

@Composable
fun StoragePanel(status: CameraStatus) {
    Column(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(Color.White)
            .border(1.dp, if (status.sdWarn) Color(0xFFE6C79A) else CameLine, RoundedCornerShape(16.dp))
            .padding(16.dp),
    ) {
        Text(stringResource(R.string.card_title), fontWeight = FontWeight.Bold, color = CameInk)
        Spacer(Modifier.height(10.dp))
        when {
            !status.card && status.sdTotal <= 0L -> {
                Text(stringResource(R.string.card_missing), color = CameMuted, fontSize = 14.sp)
            }
            status.sdTotal <= 0L -> {
                Text(stringResource(R.string.card_unknown), color = CameMuted, fontSize = 14.sp)
            }
            else -> {
                val fraction = (status.sdUsed.toFloat() / status.sdTotal.toFloat()).coerceIn(0f, 1f)
                LinearProgressIndicator(
                    progress = { fraction },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(8.dp)
                        .clip(RoundedCornerShape(4.dp)),
                    color = if (status.sdWarn) Color(0xFFC47B2B) else CameTeal,
                    trackColor = Color(0xFFF0EBE3),
                )
                Spacer(Modifier.height(8.dp))
                Text(
                    stringResource(R.string.card_free, formatBytes(status.sdFree), formatBytes(status.sdTotal)),
                    color = CameMuted,
                    fontSize = 14.sp,
                )
            }
        }
    }
}

@Composable
fun WarnBanner() {
    Text(
        stringResource(R.string.card_warn),
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(CameWarnBg)
            .padding(14.dp),
        color = CameWarn,
        fontSize = 14.sp,
        lineHeight = 20.sp,
    )
}

@Composable
fun ModeSwitch(online: Boolean, enabled: Boolean, onSelect: (Boolean) -> Unit) {
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(Color.White)
            .border(1.dp, CameLine, RoundedCornerShape(14.dp))
            .padding(4.dp),
    ) {
        ModeChip(stringResource(R.string.mode_standalone), !online, enabled, Modifier.weight(1f)) {
            onSelect(false)
        }
        ModeChip(stringResource(R.string.mode_online), online, enabled, Modifier.weight(1f)) {
            onSelect(true)
        }
    }
}

@Composable
private fun ModeChip(
    label: String,
    selected: Boolean,
    enabled: Boolean,
    modifier: Modifier,
    onClick: () -> Unit,
) {
    Box(
        modifier
            .clip(RoundedCornerShape(10.dp))
            .background(if (selected) CameTeal else Color.Transparent)
            .clickable(enabled = enabled, onClick = onClick)
            .padding(vertical = 12.dp),
        contentAlignment = Alignment.Center,
    ) {
        Text(
            label,
            color = if (selected) Color.White else CameInk,
            fontWeight = FontWeight.SemiBold,
            fontSize = 15.sp,
        )
    }
}

@Composable
fun RecordButton(recording: Boolean, onClick: () -> Unit) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Box(
            Modifier
                .size(112.dp)
                .clip(CircleShape)
                .background(if (recording) CameInk else CamePink)
                .clickable(onClick = onClick),
            contentAlignment = Alignment.Center,
        ) {
            if (recording) {
                Box(
                    Modifier
                        .size(36.dp)
                        .clip(RoundedCornerShape(8.dp))
                        .background(Color.White),
                )
            } else {
                Box(
                    Modifier
                        .size(36.dp)
                        .clip(CircleShape)
                        .background(Color.White),
                )
            }
        }
    }
}

@Composable
fun QuietButton(label: String, modifier: Modifier = Modifier, onClick: () -> Unit) {
    Box(
        modifier
            .height(48.dp)
            .clip(RoundedCornerShape(12.dp))
            .background(Color.White)
            .border(1.dp, CameLine, RoundedCornerShape(12.dp))
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp),
        contentAlignment = Alignment.Center,
    ) {
        Text(label, fontWeight = FontWeight.SemiBold, color = CameInk, fontSize = 15.sp)
    }
}

@Composable
fun PinkButton(label: String, modifier: Modifier = Modifier, onClick: () -> Unit) {
    Box(
        modifier
            .height(48.dp)
            .clip(RoundedCornerShape(12.dp))
            .background(CamePink)
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp),
        contentAlignment = Alignment.Center,
    ) {
        Text(label, fontWeight = FontWeight.Bold, color = Color.White, fontSize = 15.sp)
    }
}

@Composable
fun SectionLabel(text: String) {
    Text(text, fontWeight = FontWeight.Bold, fontSize = 16.sp, color = CameInk)
}

@Composable
fun Help(text: String) {
    Text(text, color = CameMuted, fontSize = 13.sp, lineHeight = 18.sp)
}

@Composable
fun FieldCard(body: @Composable () -> Unit) {
    Column(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(Color.White)
            .border(1.dp, CameLine, RoundedCornerShape(16.dp))
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        body()
    }
}
