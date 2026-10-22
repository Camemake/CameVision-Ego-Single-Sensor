package eu.camemake.camevision.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

val CameTeal = Color(0xFF1A6F7C)
val CamePink = Color(0xFFE84B8A)
val CamePinkPressed = Color(0xFFD63D79)
val CameBg = Color(0xFFF4EFE8)
val CameInk = Color(0xFF222222)
val CameMuted = Color(0xFF5C5C5C)
val CameLine = Color(0xFFE4DDD4)
val CameWarn = Color(0xFF8A5A12)
val CameWarnBg = Color(0xFFFFF6EA)

private val scheme = lightColorScheme(
    primary = CameTeal,
    onPrimary = Color.White,
    secondary = CamePink,
    onSecondary = Color.White,
    background = CameBg,
    onBackground = CameInk,
    surface = Color.White,
    onSurface = CameInk,
    error = CamePink,
)

@Composable
fun CameVisionTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = scheme,
        typography = MaterialTheme.typography.copy(
            bodyLarge = TextStyle(
                fontFamily = FontFamily.SansSerif,
                fontWeight = FontWeight.Normal,
                fontSize = 16.sp,
                lineHeight = 22.sp,
                color = CameInk,
            ),
        ),
        content = content,
    )
}
