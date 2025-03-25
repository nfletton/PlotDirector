package com.zygal.plotdirector

import androidx.compose.runtime.*
import androidx.compose.ui.awt.ComposeWindow
import io.grpc.ManagedChannel
import io.grpc.ManagedChannelBuilder
import io.grpc.Status
import io.grpc.StatusRuntimeException
import kotlinx.coroutines.*
import plot.PlotServiceGrpc
import plot.PlotServiceOuterClass
import java.awt.FileDialog
import java.io.FilenameFilter
import io.github.oshai.kotlinlogging.KotlinLogging


const val AXIS_STEP: Float = 0.1f
const val COMMAND_LOG_SIZE: Int = 200
const val MESSAGE_LOG_SIZE: Int = 30

open class AppState(private val window: ComposeWindow?) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private val logger = KotlinLogging.logger {}

    private var plotState by mutableStateOf(States.IDLE)
    private var plotFile = ""
    private var plotData: PlotData? = null
    private var plotChannel: ManagedChannel? = null
    private var plotJob: Job? = null

    private val commandLog = mutableListOf<String>()
    private val messageLog = mutableListOf<String>()

    private fun getStub(): PlotServiceGrpc.PlotServiceBlockingStub? {
        return plotChannel?.let { channel ->
            PlotServiceGrpc.newBlockingStub(channel)
        }
    }

    private fun logException(operation: String, e: Exception) {
        val errorMessage = when (e) {
            is StatusRuntimeException -> {
                when (e.status.code) {
                    Status.Code.INTERNAL -> "ERROR: Check NextDraw USB connection"
                    Status.Code.UNAVAILABLE -> "ERROR: Check Plot Director Server running"
                    else -> "ERROR: $operation failed"
                }
            }

            else -> "ERROR: $operation failed"
        }
        logger.error(e) { errorMessage }
    }

    private var stats = Stats(0)

    data class ButtonAction(val button: Buttons, val label: String, val onClick: () -> Unit)

    private data class Stats(val commandCount: Int) {
        var progressCount: Int = 0

        fun completedPercentage() = ((progressCount * 1.0 / commandCount) * 100).toInt()
    }

    enum class States(val label: String) {
        IDLE("Idle"),
        READY("Ready to Plot"),
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

    enum class Axis(val label: String) {
        X("x"), Y("y")
    }

    private val buttonActions = listOf(
        ButtonAction(Buttons.LOAD_PLOT, "Load Plot File") { loadPlotFile() },
        ButtonAction(Buttons.PLOT, "Plot") { startPlot() },
        ButtonAction(Buttons.QUIT, "Quit") { clearPlot() },
        ButtonAction(Buttons.CALIBRATE, "Calibrate") { switchToCalibrationMode() },
        ButtonAction(Buttons.CONTINUE, "Continue") { continuePlotting() },
        ButtonAction(Buttons.PLUS_X_AXIS, "+x") { walkCarriage(Axis.X, AXIS_STEP) },
        ButtonAction(Buttons.MINUS_X_AXIS, "-x") { walkCarriage(Axis.X, -AXIS_STEP) },
        ButtonAction(Buttons.PLUS_Y_AXIS, "+y") { walkCarriage(Axis.Y, AXIS_STEP) },
        ButtonAction(Buttons.MINUS_Y_AXIS, "-y") { walkCarriage(Axis.Y, -AXIS_STEP) },
        ButtonAction(Buttons.PLOT_ALIGN_SVG, "Alignment Plot") { plotAlignmentSvg() },
        ButtonAction(Buttons.PAUSE, "Pause") { pausePlot() },
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

    var messageLogContent by mutableStateOf("")
        private set

    var commandLogContent by mutableStateOf("")
        private set

    var statusContent by mutableStateOf("Status: ${plotState.label}")
        private set

    var activeButtons by mutableStateOf(getActiveButtons(plotState))
        private set

    private fun initializeChannel() {
        plotChannel = ManagedChannelBuilder.forAddress("localhost", 50051).usePlaintext().build()
    }

    private fun nextState(nextState: States) {
        plotState = nextState
        updateButtons()
        updateStatus()
    }

    private fun updateStatus() {
        var content = "Status: ${plotState.label}"
        if (stats.commandCount > 0) {
            content += "\nProgress: ${stats.completedPercentage()} % (${stats.progressCount}/${stats.commandCount})"
        }
        statusContent = content
    }

    private fun updateButtons() {
        activeButtons = getActiveButtons(plotState)
    }

    private fun loadPlotFile() {
        FileDialog(window, "Choose a plot file", FileDialog.LOAD).apply {
            filenameFilter = FilenameFilter { _, name -> name.endsWith(".txt") }
            isVisible = true
            file?.let { fileName ->
                plotFile = directory + fileName
                loadPlot()
                stats = Stats(plotData?.commandCount ?: 0)
                logger.info { "Plot file loaded: $plotFile" }
            }
        }
    }

    private fun loadPlot() {
        if (plotFile.isEmpty()) {
            nextState(States.IDLE)
            return
        }
        plotData = PlotData(plotFile)
        initializeChannel()
        if (initializeNextDraw()) {
            nextState(States.READY)
        }
    }

    private fun initializeNextDraw(): Boolean {
        val data = plotData ?: return false
        val stub = getStub() ?: return false

        try {
            val initRequest =
                PlotServiceOuterClass.InitializePlotRequest.newBuilder().addAllOptions(data.options)
                    .addAllDefinitions(data.definitions).build()

            val response = stub.initializePlot(initRequest)
            logMessage(response.message)

            checkNextDrawPower()

            if (!response.success) {
                logStatusMessage("Error initializing plot")
                clearPlot()
                return false
            }

            return true
        } catch (e: Exception) {
            logException("Initialize plot", e)
            clearPlot()
            return false
        }
    }

    private fun checkNextDrawPower() {
        val stub = getStub() ?: return
        try {
            val response = stub.hasPower(PlotServiceOuterClass.HasPowerRequest.newBuilder().build())
            if (!response.hasPower) logStatusMessage("Check power to NextDraw", "WARNING")
        } catch (e: Exception) {
            logException("Check NextDraw power", e)
        }
    }

    private fun switchToCalibrationMode() {
        val stub = getStub() ?: return
        try {
            val response = stub.endInteractiveContext(
                PlotServiceOuterClass.EndInteractiveContextRequest.newBuilder().build()
            )
            if (!response.success) logStatusMessage(response.message)
            nextState(States.CALIBRATING)
        } catch (e: Exception) {
            logException("Switch to calibration mode", e)
        }
    }

    private fun startPlot() {
        nextState(States.PLOTTING)
        if (plotJob == null || !plotJob!!.isActive) {
            initiatePlot(this)
        }
    }

    private fun initiatePlot(viewModel: AppState) {
        plotJob = scope.launch {
            viewModel.processCommands()
        }
    }

    private suspend fun processCommands() {
        val localPlotData = plotData ?: run {
            clearPlot()
            return
        }
        val stub = getStub() ?: run {
            logStatusMessage("Unable to connect to plotting service")
            clearPlot()
            return
        }

        while (localPlotData.hasCommands()) {
            while (plotState != States.PLOTTING) {
                delay(100)
            }

            localPlotData.nextCommand()?.let { command ->
                val commandName = command.substringBefore(' ')
                when (commandName) {
                    "pause" -> {
                        nextState(States.PAUSED)
                        logMessage(command)
                    }
                    "#" -> {
                        logCommand(command)
                    }
                    else -> {
                        try {
                            val commandRequest = PlotServiceOuterClass.CommandRequest.newBuilder()
                                .setCommand(command).build()
                            val response = stub.processCommand(commandRequest)
                            if (!response.success) logStatusMessage(response.message)
                            stats.progressCount++
                            updateStatus()
                            logCommand(command)
                        } catch (e: Exception) {
                            logException("Process command '$command'", e)
                        }
                    }
                }
            }
            delay(50)
            yield()
        }
        nextState(States.FINISHED)
    }

    private fun walkCarriage(axis: Axis, distance: Float) {
        val stub = getStub() ?: return
        try {
            val walkHomeRequest =
                PlotServiceOuterClass.WalkHomeRequest.newBuilder().setAxis(axis.label)
                    .setDistance(distance).build()

            val response = stub.walkHome(walkHomeRequest)
            if (response.success) logMessage(response.message)
            else logStatusMessage(response.message)
        } catch (e: Exception) {
            logException("Walk carriage in ${axis.label} axis", e)
        }
    }

    private fun plotAlignmentSvg() {
        resetHomePosition()
        val stub = getStub() ?: return
        try {
            val response = stub.plotAlignmentSVG(
                PlotServiceOuterClass.PlotAlignmentSVGRequest.newBuilder().build()
            )
            if (response.success) logMessage(response.message)
            else logStatusMessage(response.message)
        } catch (e: Exception) {
            logException("Plot alignment SVG", e)
        }
    }

    private fun resetHomePosition() {
        val stub = getStub() ?: return
        try {
            val response = stub.resetHomePosition(
                PlotServiceOuterClass.ResetHomePositionRequest.newBuilder().build()
            )
            if (response.success) logMessage(response.message)
            else logStatusMessage(response.message)
        } catch (e: Exception) {
            logException("Reset home position", e)
        }
    }

    private fun continuePlotting() {
        resetHomePosition()

        val stub = getStub() ?: return
        try {
            val response = stub.restoreInteractiveContext(
                PlotServiceOuterClass.RestoreInteractiveContextRequest.newBuilder().build()
            )
            if (!response.success) logStatusMessage(response.message)
            nextState(States.READY)
        } catch (e: Exception) {
            logException("Restore interactive context", e)
        }
    }

    private fun pausePlot() {
        logMessage("Plot manually paused")
        nextState(States.PAUSED)
    }

    private fun clearPlot() {
        plotJob?.cancel()
        plotData = null
        plotFile = ""
        stats = Stats(0)

        val stub = getStub()
        if (stub != null) {
            try {
                val response =
                    stub.disconnect(PlotServiceOuterClass.DisconnectRequest.newBuilder().build())
                if (response.success) logMessage(response.message)
                else logStatusMessage(response.message)
            } catch (e: Exception) {
                logException("Disconnect plot", e)
            }
        }

        logCommand("")
        nextState(States.IDLE)
        logger.info { "Plot data cleared" }
    }

    fun cleanUp() {
        scope.cancel()

        val stub = getStub()
        if (stub != null) {
            try {
                stub.disconnect(PlotServiceOuterClass.DisconnectRequest.newBuilder().build())
            } catch (e: Exception) {
                logException("Cleanup", e)
            }
        }

        logger.info { "Stopped application" }
    }

    private fun logCommand(command: String) {
        if (command.isEmpty()) {
            commandLogContent = ""
            return
        }
        commandLog.add(command)
        if (commandLog.size > COMMAND_LOG_SIZE) commandLog.removeFirst()
        commandLogContent = commandLog.joinToString("\n")
    }

    private fun logStatusMessage(message: String, status: String = "ERROR") {
        val errorMessage = "${status}: $message"
        logger.error { errorMessage }
        logMessage(errorMessage)
    }

    private fun logMessage(message: String) {
        if (message.isEmpty()) {
            messageLogContent = ""
            return
        }
        messageLog.add(message)
        if (messageLog.size > MESSAGE_LOG_SIZE) messageLog.removeFirst()
        messageLogContent = messageLog.joinToString("\n")
    }
}
