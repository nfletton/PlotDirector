package com.zygal.plotdirector

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.awt.ComposeWindow
import androidx.compose.ui.window.Window
import androidx.compose.ui.window.application
import com.zygal.plotdirector.ui.theme.PlotDirectorTheme

fun main() = application {
    val windowState = remember { mutableStateOf<ComposeWindow?>(null) }

    val viewModel = remember { AppState(windowState.value) }

    Window(
        onCloseRequest = {
            viewModel.cleanUp()
            exitApplication()
                         },
        title = viewModel.title
    ) {
        windowState.value = this.window

        PlotDirectorTheme {
            Column(modifier = Modifier.fillMaxSize()) {
                MainWindow(viewModel)
            }
        }
    }
}
