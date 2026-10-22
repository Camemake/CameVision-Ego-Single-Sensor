package eu.camemake.camevision

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import eu.camemake.camevision.ui.CameVisionApp
import eu.camemake.camevision.ui.CameVisionTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        setContent {
            CameVisionTheme {
                CameVisionApp()
            }
        }
    }
}
