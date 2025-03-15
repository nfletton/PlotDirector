package com.zygal.plotdirector

import androidx.compose.runtime.*
import androidx.compose.ui.awt.ComposeWindow
import kotlinx.coroutines.*
import java.awt.FileDialog
import java.io.FilenameFilter
import java.util.logging.Logger


open class AppState(private val window: ComposeWindow?) {
    private val viewModelScope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private val logger = Logger.getLogger("Main")

    private var plotState by mutableStateOf(States.IDLE)
    private var plotFile = ""
    private var plotData: PlotData? = null
    private var plotJob: Job? = null

    data class ButtonAction(val button: Buttons, val label: String, val onClick: () -> Unit)

    enum class States(val label: String) {
        IDLE("Idle"),
        READY("Plot File Loaded"),
        PLOTTING("Plotting"),
        PAUSED("Plot Paused"),
        CALIBRATING("Calibrating Home Position"),
    }

    enum class Buttons {
        LOAD_PLOT,
        PLOT,
        QUIT,
        CALIBRATE,
        PLUS_X_AXIS,
        MINUS_X_AXIS,
        PLUS_Y_AXIS,
        MINUS_Y_AXIS,
        PLOT_ALIGN_SVG,
        PAUSE,
    }

    val buttonActions = listOf(
        ButtonAction(Buttons.LOAD_PLOT, "Load Plot File") { openPlotFile() },
        ButtonAction(Buttons.PLOT, "Plot") { nextState(States.PLOTTING) },
        ButtonAction(Buttons.QUIT, "Quit") { nextState(States.IDLE) },
        ButtonAction(Buttons.CALIBRATE, "Calibrate") { nextState(States.CALIBRATING) },
        ButtonAction(Buttons.PLUS_X_AXIS, "+x") { logger.info("Increment x axis") },
        ButtonAction(Buttons.MINUS_X_AXIS, "-x") { logger.info("Decrement x axis") },
        ButtonAction(Buttons.PLUS_Y_AXIS, "+y") { logger.info("Increment y axis") },
        ButtonAction(Buttons.MINUS_Y_AXIS, "-y") { logger.info("Decrement y axis") },
        ButtonAction(
            Buttons.PLOT_ALIGN_SVG,
            "Alignment Plot"
        ) { logger.info("Output alignment plot") },
        ButtonAction(Buttons.PAUSE, "Pause") { nextState(States.PAUSED) },
    )

    val stateButtonMapping = mapOf(
        States.IDLE to listOf(Buttons.LOAD_PLOT),
        States.READY to listOf(Buttons.PLOT, Buttons.CALIBRATE, Buttons.QUIT),
        States.PLOTTING to listOf(Buttons.PAUSE),
        States.PAUSED to listOf(Buttons.PLOT, Buttons.CALIBRATE, Buttons.QUIT),
        States.CALIBRATING to listOf(
            Buttons.PLUS_X_AXIS,
            Buttons.MINUS_X_AXIS,
            Buttons.PLUS_Y_AXIS,
            Buttons.MINUS_Y_AXIS,
            Buttons.PLOT_ALIGN_SVG,
            Buttons.PLOT,
            Buttons.QUIT
        ),
    )

    private fun getActiveButtons(state: States): List<ButtonAction> =
        stateButtonMapping[state]?.map { button ->
            buttonActions.first { it.button == button }
        } ?: emptyList()


    var title by mutableStateOf("Plot Director")
        private set

    var leftLogContent by mutableStateOf("")
        private set

    var rightLogContent by mutableStateOf("")
        private set

    var activeButtons by mutableStateOf(getActiveButtons(plotState))
        private set


    private fun nextState(nextState: States) {
        when (nextState) {
            States.IDLE -> clearPlot()
            States.READY -> initPlot()
            States.PLOTTING -> {
                if (plotJob == null || !plotJob!!.isActive) {
                    startPlot(this)
                }
            }
            States.PAUSED -> {}
            States.CALIBRATING -> {}
        }
        plotState = nextState
        updateButtons()
    }

    private fun initPlot() {
        if (plotFile.isEmpty()) {
            nextState(States.IDLE)
            return
        }
        plotData = PlotData(plotFile)
        logger.info("Plot data loaded")
    }

    private fun openPlotFile() {
        FileDialog(window, "Choose a plot file", FileDialog.LOAD).apply {
            filenameFilter = FilenameFilter { _, name -> name.endsWith(".txt") }
            isVisible = true
            file?.let { fileName ->
                title = "Plot File: $fileName, Status: ${plotState}"
                plotFile = directory + fileName
                nextState(States.READY)
            }
        }
    }

    private fun clearPlot() {
        plotData = null
        plotFile = ""
    }

    fun clearLeftLog() {
        leftLogContent = ""
    }

    fun clearRightLog() {
        rightLogContent = ""
    }

    fun updateButtons() {
        activeButtons = getActiveButtons(plotState)
    }

    suspend fun processData() {
        for (i in 1..100) {
            delay(50)
            while (plotState == States.PAUSED) {
                logger.info("Paused at: $i")
                delay(1000)
            }
            logger.info("Processing: $i")
        }
        nextState(States.IDLE)
    }


    fun startPlot(viewModel: AppState) {
        plotJob = viewModelScope.launch {
            viewModel.processData()
        }
    }

    fun cleanUp() {
        logger.info("Stopping application...")
        viewModelScope.cancel()
    }
}
