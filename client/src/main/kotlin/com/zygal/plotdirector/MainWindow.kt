package com.zygal.plotdirector

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

@Composable
fun MainWindow(viewModel: AppState) {

    Column(modifier = Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background)) {
        // Top button bar
            ButtonBar(
                buttons = viewModel.activeButtons,
                modifier = Modifier.fillMaxWidth()
                    .background(Color.White)
            )

        // Split view for logging widgets
        Row(
            modifier = Modifier.fillMaxSize().weight(1f).padding(8.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Left logging widget
            LogWidget(
                title = "Messages",
                content = viewModel.messagesLogContent,
                modifier = Modifier.fillMaxHeight().weight(1f)
            )

            // Right logging widget
            LogWidget(
                title = "Command Log",
                content = viewModel.commandLogContent,
                modifier = Modifier.fillMaxHeight().weight(1f)
            )
        }
    }
}

@Composable
fun ButtonBar(
    buttons: List<AppState.ButtonAction>,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        color = MaterialTheme.colorScheme.surfaceVariant,
        tonalElevation = 4.dp
    ) {
        Row(
            modifier = Modifier.padding(8.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            buttons.forEach { buttonAction ->
                Button(
                    onClick = buttonAction.onClick,
                    colors = ButtonDefaults.buttonColors()
                ) {
                    Text(buttonAction.label)
                }
            }
        }
    }
}

@Composable
fun LogWidget(
    title: String,
    content: String,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 2.dp
    ) {
        Column(
            modifier = Modifier.fillMaxSize().padding(8.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleMedium
                )
            }

            Box(
                modifier = Modifier.fillMaxSize().padding(top = 8.dp).border(1.dp, MaterialTheme.colorScheme.outline)
            ) {
                val verticalScrollState = rememberScrollState()
                val horizontalScrollState = rememberScrollState()

                // Auto-scroll to bottom when content changes
                LaunchedEffect(content) {
                    if (content.isNotEmpty()) {
                        verticalScrollState.animateScrollTo(verticalScrollState.maxValue)
                    }
                }

                TextField(
                    value = content,
                    onValueChange = { },
                    modifier = Modifier
                        .fillMaxSize()
                        .horizontalScroll(horizontalScrollState)
                        .verticalScroll(verticalScrollState),
                    readOnly = true,
                    maxLines = Int.MAX_VALUE,
                    colors = TextFieldDefaults.colors(),
                    textStyle = MaterialTheme.typography.bodySmall,
                )

                VerticalScrollbar(
                    modifier = Modifier.align(Alignment.CenterEnd),
                    adapter = rememberScrollbarAdapter(verticalScrollState)
                )

                HorizontalScrollbar(
                    modifier = Modifier.align(Alignment.BottomCenter),
                    adapter = rememberScrollbarAdapter(horizontalScrollState)
                )
            }
        }
    }
}
