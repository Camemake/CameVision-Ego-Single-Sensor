package eu.camemake.camevision.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import eu.camemake.camevision.CameVisionModel
import eu.camemake.camevision.LinkState
import eu.camemake.camevision.R

@Composable
fun CardScreen(
    model: CameVisionModel,
    link: LinkState,
    banner: String,
    onSend: (String) -> Unit,
) {
    var confirmClear by rememberSaveable { mutableStateOf(false) }
    var confirmDelete by rememberSaveable { mutableStateOf("") }
    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp, vertical = 8.dp),
    ) {
        Text(stringResource(R.string.card_title), fontWeight = FontWeight.ExtraBold, fontSize = 32.sp, color = CameInk)
        Spacer(Modifier.height(16.dp))
        StoragePanel(link.status)
        if (link.status.sdWarn) {
            Spacer(Modifier.height(10.dp))
            WarnBanner()
        }
        val shown = bannerText(banner.ifBlank { link.status.error })
        if (shown != null) {
            Spacer(Modifier.height(10.dp))
            Text(shown.first, color = if (shown.second) CameTeal else CamePink, fontSize = 14.sp)
        }
        Spacer(Modifier.height(8.dp))
        TextButton(
            onClick = { confirmClear = true },
            enabled = !link.status.recording,
            modifier = Modifier.align(Alignment.End),
        ) {
            Text(stringResource(R.string.clear_card), color = CamePink, fontWeight = FontWeight.SemiBold)
        }
        if (link.sessions.isEmpty()) {
            Text(stringResource(R.string.no_sessions), color = CameMuted, modifier = Modifier.padding(top = 12.dp))
        }
        link.sessions.forEach { session ->
            Spacer(Modifier.height(10.dp))
            Column(Modifier.fillMaxWidth().panel().padding(14.dp)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(formatSession(session.id), fontWeight = FontWeight.Bold, color = CameInk)
                    if (session.sent) {
                        Text(stringResource(R.string.sent), color = CameTeal, fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
                    }
                }
                Spacer(Modifier.height(4.dp))
                val mode = if (session.mode == "online") {
                    stringResource(R.string.mode_online)
                } else {
                    stringResource(R.string.mode_standalone)
                }
                Text(
                    stringResource(R.string.session_meta, mode, formatBytes(session.bytes)),
                    color = CameMuted,
                    fontSize = 14.sp,
                )
                Spacer(Modifier.height(10.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    QuietButton(stringResource(R.string.send)) { onSend(session.id) }
                    QuietButton(stringResource(R.string.remove)) { confirmDelete = session.id }
                }
            }
        }
        Spacer(Modifier.height(16.dp))
    }
    if (confirmClear) {
        AlertDialog(
            onDismissRequest = { confirmClear = false },
            title = { Text(stringResource(R.string.clear_title)) },
            text = { Text(stringResource(R.string.clear_body)) },
            confirmButton = {
                TextButton(onClick = {
                    confirmClear = false
                    model.clearCard()
                }) { Text(stringResource(R.string.clear_go), color = CamePink) }
            },
            dismissButton = {
                TextButton(onClick = { confirmClear = false }) { Text(stringResource(R.string.cancel)) }
            },
        )
    }
    if (confirmDelete.isNotEmpty()) {
        AlertDialog(
            onDismissRequest = { confirmDelete = "" },
            title = { Text(stringResource(R.string.remove_title)) },
            text = { Text(stringResource(R.string.remove_body)) },
            confirmButton = {
                TextButton(onClick = {
                    val id = confirmDelete
                    confirmDelete = ""
                    model.deleteSession(id)
                }) { Text(stringResource(R.string.remove), color = CamePink) }
            },
            dismissButton = {
                TextButton(onClick = { confirmDelete = "" }) { Text(stringResource(R.string.cancel)) }
            },
        )
    }
}

private fun Modifier.panel() = this
    .clip(RoundedCornerShape(16.dp))
    .background(Color.White)
    .border(1.dp, CameLine, RoundedCornerShape(16.dp))
