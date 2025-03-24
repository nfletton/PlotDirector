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
import java.util.logging.Logger

const val AXIS_STEP: Float = 0.1f
const val COMMAND_LOG_SIZE: Int = 200
const val MESSAGE_LOG_SIZE: Int = 30

open class AppState(private val window: ComposeWindow?) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private val logger = Logger.getLogger("Main")

    private var plotState by mutableStateOf(States.IDLE)
    private var plotFile = ""
    private var plotData: PlotData? = null
    private var plotChannel: ManagedChannel? = null
    private var plotJob: Job? = null

    private val commandLog = mutableListOf<String>()
    private val messageLog = mutableListOf<String>()
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
        ButtonAction(Buttons.LOAD_PLOT, "Load Plot File") { openPlotFile() },
        ButtonAction(Buttons.PLOT, "Plot") { startPlot() },
        ButtonAction(Buttons.QUIT, "Quit") { clearPlot() },
        ButtonAction(Buttons.CALIBRATE, "Calibrate") { switchToCalibrationMode() },
        ButtonAction(Buttons.CONTINUE, "Continue") { continuePlotting() },
        ButtonAction(Buttons.PLUS_X_AXIS, "+x") { walkCarriage(Axis.X, AXIS_STEP) },
        ButtonAction(Buttons.MINUS_X_AXIS, "-x") { walkCarriage(Axis.X, -AXIS_STEP) },
        ButtonAction(Buttons.PLUS_Y_AXIS, "+y") { walkCarriage(Axis.Y, AXIS_STEP)},
        ButtonAction(Buttons.MINUS_Y_AXIS, "-y") { walkCarriage(Axis.Y, -AXIS_STEP) },
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

    var messageLogContent by mutableStateOf("")
        private set

    var commandLogContent by mutableStateOf("")
        private set

    var statusContent by mutableStateOf("Status: ${plotState.label}")
        private set

    var activeButtons by mutableStateOf(getActiveButtons(plotState))
        private set

    private fun initializeChannel() {
        plotChannel = ManagedChannelBuilder
            .forAddress("localhost", 50051)
            .usePlaintext()
            .build()
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

    private fun openPlotFile() {
        FileDialog(window, "Choose a plot file", FileDialog.LOAD).apply {
            filenameFilter = FilenameFilter { _, name -> name.endsWith(".txt") }
            isVisible = true
            file?.let { fileName ->
                plotFile = directory + fileName
                loadPlot()
                stats = Stats(plotData?.commandCount ?: 0)
                logger.info("Plot file loaded: $plotFile")
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
            logger.info("Plot data loaded. NextDraw Initialized.")
        }
    }

    private fun initializeNextDraw(): Boolean {
        plotData?.let { data ->
            plotChannel?.let { channel ->

                try {
                    val stub = PlotServiceGrpc.newBlockingStub(channel)
                    val initRequest = PlotServiceOuterClass.InitializePlotRequest.newBuilder()
                        .addAllOptions(data.options)
                        .addAllDefinitions(data.definitions)
                        .build()

                    val response = stub.initializePlot(initRequest)
                    updateMessageLog(response.message)

                    checkNextDrawPower()

                    if (!response.success) {
                        logger.severe("Error initializing plot: ${response.message}")
                        clearPlot()
                        return false
                    }

                    logger.info("NextDraw Initialized")
                    return true
                } catch (e: StatusRuntimeException) {
                    logger.severe("Error initializing plot: ${e.message}")
                    val errorMessage = when (e.status.code) {
                        Status.Code.INTERNAL -> "ERROR: Check NextDraw USB connection"
                        Status.Code.UNAVAILABLE -> "ERROR: Check Plot Director Server running"
                        else -> "ERROR: ${e.message}"
                    }
                    updateMessageLog(errorMessage)
                    clearPlot()
                    return false
                }
            }
        }
        return false
    }

    private fun checkNextDrawPower() {
        val stub = PlotServiceGrpc.newBlockingStub(plotChannel!!)
        val response = stub.hasPower(PlotServiceOuterClass.HasPowerRequest.newBuilder().build())
        if (!response.hasPower) {
            updateMessageLog("WARNING: Check power to NextDraw")
        }
    }

    private fun switchToCalibrationMode() {
        val stub = PlotServiceGrpc.newBlockingStub(plotChannel!!)
        val response = stub.endInteractiveContext(PlotServiceOuterClass.EndInteractiveContextRequest.newBuilder().build())
        if (!response.success) {
            logger.severe("Error ending interactive context: ${response.message}")
            updateMessageLog("ERROR: ${response.message}")
        }
        nextState(States.CALIBRATING)
        logger.info("Switched to calibration mode")
   }


    private fun startPlot() {
        nextState(States.PLOTTING)
        if (plotJob == null || !plotJob!!.isActive) {
            initiatePlot(this)
        }
    }

    private fun initiatePlot(viewModel: AppState) {
        plotJob = scope.launch {
            viewModel.processData()
        }
    }

    private suspend fun processData() {
        val localPlotData = plotData ?: run {
            clearPlot()
            return
        }
        val stub = PlotServiceGrpc.newBlockingStub(plotChannel)

        while (localPlotData.hasCommands()) {
            while (plotState != States.PLOTTING) {
                delay(100)
            }

            localPlotData.nextCommand()?.let { command ->
                val commandName = command.substringBefore(' ')
                when (commandName) {
                    "pause" -> {
                        nextState(States.PAUSED)
                        updateMessageLog(command)
                    }

                    else -> {
                        try {
                            val commandRequest = PlotServiceOuterClass.CommandRequest.newBuilder()
                                .setCommand(command)
                                .build()
                            val commandResponse = stub.processCommand(commandRequest)
                            if (!commandResponse.success) {
                                logger.severe("Error processing command '$command'")
                            }
                            stats.progressCount++
                            updateStatus()
                            updateCommandLog(command)
                            logger.info("Command: $command -> Response: ${commandResponse.message}")
                        } catch (e: Exception) {
                            logger.severe("Error processing command '$command': ${e.message}")
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
        try {
            val stub = PlotServiceGrpc.newBlockingStub(plotChannel)

            val walkHomeRequest = PlotServiceOuterClass.WalkHomeRequest.newBuilder()
                .setAxis(axis.label)
                .setDistance(distance)
                .build()

            val walkHomeResponse = stub.walkHome(walkHomeRequest)
            updateMessageLog(walkHomeResponse.message)
        } catch (e: Exception) {
            logger.severe("Error walking home position in ${axis.label} axis: ${e.message}")
        }
    }

    private fun plotAlignmentSvg() {
        resetHomePosition()
        val stub = PlotServiceGrpc.newBlockingStub(plotChannel)
        stub.plotAlignmentSVG(PlotServiceOuterClass.PlotAlignmentSVGRequest.newBuilder().build())
        logger.info("Plotted alignment SVG")
    }

    private fun resetHomePosition() {
        val stub = PlotServiceGrpc.newBlockingStub(plotChannel)
        val resetHomeResponse = stub.resetHomePosition(PlotServiceOuterClass.ResetHomePositionRequest.newBuilder().build())
        if (!resetHomeResponse.success) {
            logger.severe("Error resetting home position: ${resetHomeResponse.message}")
        }
        logger.info("Home position reset")
    }

    private fun continuePlotting() {
        resetHomePosition()
        val stub = PlotServiceGrpc.newBlockingStub(plotChannel)
        stub.restoreInteractiveContext(PlotServiceOuterClass.RestoreInteractiveContextRequest.newBuilder().build())

        nextState(States.READY)
    }

    private fun clearPlot() {
        plotJob?.cancel()
        plotData = null
        plotFile = ""
        stats = Stats(0)
        val stub = PlotServiceGrpc.newBlockingStub(plotChannel)
        stub.disconnect(PlotServiceOuterClass.DisconnectRequest.newBuilder().build())
        updateCommandLog("")
        nextState(States.IDLE)
        logger.info("Plot data cleared")
    }

    fun cleanUp() {
        scope.cancel()
        val stub = PlotServiceGrpc.newBlockingStub(plotChannel)
        stub.disconnect(PlotServiceOuterClass.DisconnectRequest.newBuilder().build())
        logger.info("Stopped application")
    }

    private fun updateCommandLog(command: String) {
        if (command.isEmpty()) {
            commandLogContent = ""
            return
        }
        commandLog.add(command)
        if (commandLog.size > COMMAND_LOG_SIZE) commandLog.removeFirst()
        commandLogContent = commandLog.joinToString("\n")
    }

    private fun updateMessageLog(message: String) {
        if (message.isEmpty()) {
            commandLogContent = ""
            return
        }
        messageLog.add(message)
        if (messageLog.size > MESSAGE_LOG_SIZE) messageLog.removeFirst()
        messageLogContent = messageLog.joinToString("\n")
    }
}
