package com.zygal.plotdirector

import androidx.compose.runtime.*
import androidx.compose.ui.awt.ComposeWindow
import kotlinx.coroutines.*
import java.awt.FileDialog
import java.io.FilenameFilter
import java.util.logging.Logger

const val AXIS_STEP: Double = 0.1
const val COMMAND_LOG_SIZE: Int = 200

open class AppState(private val window: ComposeWindow?) {
    private val viewModelScope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private val logger = Logger.getLogger("Main")

    private var plotState by mutableStateOf(States.IDLE)
    private var plotFile = ""
    private var plotData: PlotData? = null
    private var plotJob: Job? = null

    private val commandLog = mutableListOf<String>()
    private val messageLog = mutableListOf<String>()

    data class ButtonAction(val button: Buttons, val label: String, val onClick: () -> Unit)

    enum class States(val label: String) {
        IDLE("Idle"),
        READY("Plot File Loaded"),
        PLOTTING("Plotting"),
        PAUSED("Plot Paused"),
        CALIBRATING("Calibrating Home Position"),
        FINISHED("Plot Finished")
    }

    enum class Buttons {
        LOAD_PLOT,
        PLOT,
        QUIT,
        CALIBRATE,
        CONTINUE,
        PLUS_X_AXIS,
        MINUS_X_AXIS,
        PLUS_Y_AXIS,
        MINUS_Y_AXIS,
        PLOT_ALIGN_SVG,
        PAUSE,
    }

    enum class Axis {
        X, Y
    }

    private val buttonActions = listOf(
        ButtonAction(Buttons.LOAD_PLOT, "Load Plot File") { openPlotFile() },
        ButtonAction(Buttons.PLOT, "Plot") { startPlot() },
        ButtonAction(Buttons.QUIT, "Quit") { clearPlot() },
        ButtonAction(Buttons.CALIBRATE, "Calibrate") { nextState(States.CALIBRATING) },
        ButtonAction(Buttons.CONTINUE, "Continue") { continuePlotting() },
        ButtonAction(Buttons.PLUS_X_AXIS, "+x") { walkCarriage(AXIS_STEP, Axis.X) },
        ButtonAction(Buttons.MINUS_X_AXIS, "-x") { walkCarriage(-AXIS_STEP, Axis.X) },
        ButtonAction(Buttons.PLUS_Y_AXIS, "+y") { walkCarriage(AXIS_STEP, Axis.Y) },
        ButtonAction(Buttons.MINUS_Y_AXIS, "-y") { walkCarriage(-AXIS_STEP, Axis.Y)},
        ButtonAction(
            Buttons.PLOT_ALIGN_SVG,
            "Alignment Plot"
        ) { plotAlignmentSvg() },
        ButtonAction(Buttons.PAUSE, "Pause") { nextState(States.PAUSED) },
    )

    private val stateButtonMapping = mapOf(
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
            Buttons.CONTINUE,
        ),
        States.FINISHED to listOf(Buttons.QUIT)
    )

    private fun getActiveButtons(state: States): List<ButtonAction> =
        stateButtonMapping[state]?.map { button ->
            buttonActions.first { it.button == button }
        } ?: emptyList()


    var title by mutableStateOf("Plot Director")
        private set

    var messagesLogContent by mutableStateOf("")
        private set

    var commandLogContent by mutableStateOf("")
        private set

    var activeButtons by mutableStateOf(getActiveButtons(plotState))
        private set


    private fun nextState(nextState: States) {
        plotState = nextState
        updateButtons()
    }

    private fun updateButtons() {
        activeButtons = getActiveButtons(plotState)
    }

    private fun openPlotFile() {
        FileDialog(window, "Choose a plot file", FileDialog.LOAD).apply {
            filenameFilter = FilenameFilter { _, name -> name.endsWith(".txt") }
            isVisible = true
            file?.let { fileName ->
                title = "Plot File: $fileName, Status: $plotState"
                plotFile = directory + fileName
                loadPlot()
            }
        }
    }

    private fun loadPlot() {
        if (plotFile.isEmpty()) {
            nextState(States.IDLE)
            return
        }
        plotData = PlotData(plotFile)
        nextState(States.READY)
        logger.info("Plot data loaded")
    }

    private fun startPlot() {
        nextState(States.PLOTTING)
        if (plotJob == null || !plotJob!!.isActive) {
            initiatePlot(this)
        }
    }

    private fun initiatePlot(viewModel: AppState) {
        plotJob = viewModelScope.launch {
            viewModel.processData()
        }
    }

    private suspend fun processData() {
        val localPlotData = plotData ?: run {
            clearPlot()
            return
        }
        while (localPlotData.hasCommands()) {
            while (plotState != States.PLOTTING) {
                delay(100)
            }

            localPlotData.nextCommand()?.let { command ->
                updateCommandLog(command)
            }
            delay(50)
            yield()
        }
       nextState(States.FINISHED)
    }

    private fun walkCarriage(distance: Double, axis: Axis) {
//        todo: implement
        when (axis) {
            Axis.X -> {
                logger.info("Walk carriage x axis ${distance}mm")
            }
            Axis.Y -> {
                logger.info("Walk carriage y axis ${distance}mm")
            }
        }
    }

    private fun plotAlignmentSvg() {
        logger.info("Plotting alignment SVG")
//        todo: implement
    }

    private fun continuePlotting() {
        nextState(States.READY)
//        todo: implement
        logger.info("Reset home position")
    }

    private fun clearPlot() {
        plotJob?.cancel()
        plotData = null
        plotFile = ""
        // todo: clear log windows
        nextState(States.IDLE)
        logger.info("Plot data cleared")
    }

    fun cleanUp() {
        viewModelScope.cancel()
        logger.info("Stopped application")
    }

    private fun updateCommandLog(command: String) {
        if (command.isEmpty()) return
        commandLog.add(command)
        if (commandLog.size > COMMAND_LOG_SIZE) commandLog.removeFirst()
        commandLogContent = commandLog.joinToString("\n")
    }

}
