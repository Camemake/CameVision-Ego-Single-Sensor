package eu.camemake.camevision.ui

import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.BitmapFactory
import android.provider.Settings
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.WindowInsetsSides
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.only
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PhotoCamera
import androidx.compose.material.icons.filled.SdCard
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Checkbox
import androidx.compose.material3.Icon
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import eu.camemake.camevision.CameVisionModel
import eu.camemake.camevision.R
import eu.camemake.camevision.TransferHub
import eu.camemake.camevision.isServerTemplate
import kotlinx.coroutines.delay
import kotlin.math.max

private enum class Tab { Record, Card, Setup }

@Composable
fun CameVisionApp(model: CameVisionModel = viewModel()) {
    val link by model.link.state.collectAsState()
    val banner by model.banner.collectAsState()
    val previewUntil by model.previewUntil.collectAsState()
    val preview by model.previewImage.collectAsState()
    val transfer by TransferHub.state.collectAsState()
    val saved by model.saved.collectAsState()
    var tabIndex by rememberSaveable { mutableIntStateOf(0) }
    val tab = when (tabIndex) {
        1 -> Tab.Card
        2 -> Tab.Setup
        else -> Tab.Record
    }
    var sendTarget by rememberSaveable { mutableStateOf("") }
    var removeAfter by rememberSaveable { mutableStateOf(false) }
    val context = LocalContext.current
    val previewOpen = previewUntil > System.currentTimeMillis()

    val permissions = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions(),
    ) { result ->
        val allowed = model.btPermissions().all { result[it] == true }
        if (allowed) model.findCamera() else model.banner.value = "permission"
    }

    fun connect() {
        tabIndex = 2
        val needed = model.btPermissions().toMutableList()
        model.notifPermission()?.let { needed.add(it) }
        val missing = needed.any {
            context.checkSelfPermission(it) != PackageManager.PERMISSION_GRANTED
        }
        if (missing) permissions.launch(needed.toTypedArray()) else model.findCamera()
    }

    fun askSend(id: String) {
        if (isServerTemplate(saved.server)) {
            model.banner.value = "server_template"
        } else {
            removeAfter = false
            sendTarget = id
        }
    }

    BackHandler(enabled = previewOpen) { model.stopPreview() }

    Box(Modifier.fillMaxSize().background(CameBg)) {
        Scaffold(
            containerColor = CameBg,
            contentWindowInsets = WindowInsets(0, 0, 0, 0),
            topBar = {
                BrandBar(
                    connected = link.transport.isNotEmpty(),
                    name = link.name,
                    onConnect = { connect() },
                )
            },
            bottomBar = {
                Column(
                    Modifier
                        .fillMaxWidth()
                        .background(Color.White)
                        .windowInsetsPadding(
                            WindowInsets.safeDrawing.only(WindowInsetsSides.Bottom + WindowInsetsSides.Horizontal),
                        ),
                ) {
                    Row(Modifier.fillMaxWidth().heightIn(min = 64.dp)) {
                        BottomItem(stringResource(R.string.tab_record), Icons.Filled.PhotoCamera, tab == Tab.Record, Modifier.weight(1f)) { tabIndex = 0 }
                        BottomItem(stringResource(R.string.tab_card), Icons.Filled.SdCard, tab == Tab.Card, Modifier.weight(1f)) { tabIndex = 1 }
                        BottomItem(stringResource(R.string.tab_setup), Icons.Filled.Settings, tab == Tab.Setup, Modifier.weight(1f)) { tabIndex = 2 }
                    }
                }
            },
        ) { padding ->
            Box(
                Modifier
                    .padding(padding)
                    .windowInsetsPadding(WindowInsets.safeDrawing.only(WindowInsetsSides.Horizontal)),
            ) {
                when (tab) {
                    Tab.Record -> RecordScreen(model, link, transfer, banner, { connect() }) { askSend("*") }
                    Tab.Card -> CardScreen(model, link, banner) { askSend(it) }
                    Tab.Setup -> SetupScreen(
                        model = model,
                        link = link,
                        banner = banner,
                        bluetoothOn = model.link.bluetoothOn(),
                        onPair = { connect() },
                        onPick = { model.choose(it) },
                        onForget = { model.forget() },
                        onBluetooth = {
                            context.startActivity(Intent(Settings.ACTION_BLUETOOTH_SETTINGS))
                        },
                    )
                }
            }
        }
        if (previewOpen) {
            PreviewOverlay(preview, previewUntil) { model.stopPreview() }
        }
    }

    if (sendTarget.isNotEmpty()) {
        AlertDialog(
            onDismissRequest = { sendTarget = "" },
            title = { Text(stringResource(R.string.send_title)) },
            text = {
                Column {
                    Text(stringResource(if (sendTarget == "*") R.string.send_body else R.string.send_one_body))
                    Spacer(Modifier.height(8.dp))
                    Text(saved.server, color = CameTeal, fontSize = 13.sp)
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Checkbox(checked = removeAfter, onCheckedChange = { removeAfter = it })
                        Text(stringResource(R.string.remove_after), fontSize = 14.sp)
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    val id = sendTarget
                    sendTarget = ""
                    model.send(id, removeAfter)
                }) {
                    Text(stringResource(R.string.send_go), color = CamePink, fontWeight = FontWeight.Bold)
                }
            },
            dismissButton = {
                TextButton(onClick = { sendTarget = "" }) { Text(stringResource(R.string.cancel)) }
            },
        )
    }
}

@Composable
private fun BrandBar(connected: Boolean, name: String, onConnect: () -> Unit) {
    Row(
        Modifier
            .fillMaxWidth()
            .windowInsetsPadding(WindowInsets.safeDrawing.only(WindowInsetsSides.Top + WindowInsetsSides.Horizontal))
            .padding(horizontal = 20.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Image(
            painter = painterResource(R.drawable.camemake_logo),
            contentDescription = stringResource(R.string.brand),
            modifier = Modifier.height(22.dp),
            contentScale = ContentScale.Fit,
        )
        Spacer(Modifier.weight(1f))
        Row(
            Modifier
                .clip(RoundedCornerShape(20.dp))
                .background(Color.White)
                .border(1.dp, CameLine, RoundedCornerShape(20.dp))
                .clickable(onClick = onConnect)
                .padding(horizontal = 12.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(
                Modifier
                    .size(8.dp)
                    .clip(CircleShape)
                    .background(if (connected) CameTeal else Color(0xFFC8C0B6)),
            )
            Spacer(Modifier.size(8.dp))
            Text(
                if (connected && name.isNotBlank()) name else stringResource(R.string.not_connected),
                fontSize = 13.sp,
                fontWeight = FontWeight.SemiBold,
                color = CameInk,
                maxLines = 1,
            )
        }
    }
}

@Composable
private fun BottomItem(
    label: String,
    icon: ImageVector,
    selected: Boolean,
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {
    val tint = if (selected) CameTeal else CameMuted
    Column(
        modifier
            .clickable(onClick = onClick)
            .padding(vertical = 8.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Icon(icon, contentDescription = label, tint = tint, modifier = Modifier.size(22.dp))
        Text(label, color = tint, fontSize = 12.sp, fontWeight = if (selected) FontWeight.Bold else FontWeight.Medium)
    }
}

@Composable
private fun PreviewOverlay(jpeg: ByteArray?, until: Long, onClose: () -> Unit) {
    var now by remember { mutableLongStateOf(System.currentTimeMillis()) }
    LaunchedEffect(until) {
        while (System.currentTimeMillis() < until) {
            now = System.currentTimeMillis()
            delay(250)
        }
        onClose()
    }
    val bitmap: ImageBitmap? = remember(jpeg) {
        if (jpeg == null) {
            null
        } else {
            BitmapFactory.decodeByteArray(jpeg, 0, jpeg.size)?.asImageBitmap()
        }
    }
    val left = max(0, ((until - now) / 1000).toInt())
    Box(
        Modifier
            .fillMaxSize()
            .background(Color(0xFF161616))
            .windowInsetsPadding(WindowInsets.safeDrawing)
            .clickable(onClick = {}),
    ) {
        Column(
            Modifier
                .fillMaxSize()
                .padding(20.dp),
        ) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(stringResource(R.string.preview_title), color = Color.White, fontWeight = FontWeight.Bold)
                Text(stringResource(R.string.preview_left, left), color = Color.White, fontWeight = FontWeight.Bold)
            }
            Box(Modifier.weight(1f).fillMaxWidth(), contentAlignment = Alignment.Center) {
                if (bitmap != null) {
                    Image(
                        bitmap = bitmap,
                        contentDescription = stringResource(R.string.preview_title),
                        modifier = Modifier.fillMaxWidth(),
                        contentScale = ContentScale.Fit,
                    )
                } else {
                    Text(
                        stringResource(R.string.preview_wait),
                        color = Color.White,
                        textAlign = TextAlign.Center,
                    )
                }
            }
            Spacer(Modifier.height(12.dp))
            QuietButton(stringResource(R.string.close), Modifier.fillMaxWidth(), onClose)
        }
    }
}
