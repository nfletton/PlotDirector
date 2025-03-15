package com.zygal.plotdirector

import io.grpc.ManagedChannel
import io.grpc.ManagedChannelBuilder
import kotlinx.coroutines.runBlocking
import org.junit.FixMethodOrder
import plot.PlotServiceGrpc
import plot.PlotServiceOuterClass
import java.util.concurrent.TimeUnit
import java.util.logging.Level
import java.util.logging.Logger
import kotlin.test.*

import org.junit.runners.MethodSorters

@FixMethodOrder(MethodSorters.NAME_ASCENDING)
class PlotServiceTest {

    private lateinit var channel: ManagedChannel
    private val logger = Logger.getLogger("Main")

    @BeforeTest
    fun setup() {
        channel = ManagedChannelBuilder
            .forAddress("localhost", 50051)
            .usePlaintext()
            .build()
        logger.info("Channel created")
    }

    @AfterTest
    fun teardown() {
        channel.shutdown().awaitTermination(5, TimeUnit.SECONDS)
        logger.info("Channel shutdown completed")
    }

    @Test
    fun `10 initialize nextdraw`() = runBlocking {
        try {
            val stub = PlotServiceGrpc.newBlockingStub(channel)

            // Initial configuration options
            val initOptions = listOf(
                "model 2",
                "penlift 3",
                "units 2",
                "pen_pos_up 47",
                "pen_pos_down 33",
                "accel 50",
                "speed_pendown 10",
                "speed_penup 35"
            )

            // Command definitions
            val initDefinitions = listOf(
                "go_home moveto 0 0",
                "draw_square moveto 0 0 | lineto 10 0 | lineto 10 10 | lineto 0 10 | lineto 0 0"
            )

            // Build the InitializePlot request
            val request = PlotServiceOuterClass.InitializePlotRequest.newBuilder()
                .addAllOptions(initOptions)
                .addAllDefinitions(initDefinitions)
                .build()

            // Call initializePlot on the stub
            val response = stub.initializePlot(request)

            logger.info("Initializing plot")
            logger.info("Response: ${response.message}")
            logger.info("Success: ${response.success}")

            assertTrue(response.success)
        } catch (e: Exception) {
            logger.log(Level.SEVERE, "Error initializing plot: ${e.message}", e)
            fail("Error initializing plot: ${e.message}")
        }
    }

    @Test
    fun `20 check nextdraw power`() {
        // Check power after initialization
        val stub = PlotServiceGrpc.newBlockingStub(channel)
        val powerResponse = stub.hasPower(PlotServiceOuterClass.HasPowerRequest.newBuilder().build())
        logger.info("Checking power after initialization: ${powerResponse.hasPower}")
        assertTrue(powerResponse.hasPower, "Plotter does not have power after initialization")
    }

    @Test
    fun `30 test drawing commands`() {
        val stub = PlotServiceGrpc.newBlockingStub(channel)

        val commands = listOf(
            "penup",
            "moveto 20 20",
            "pendown",
            "lineto 40 40",
            "draw_path [[50,50],[70,50],[70,70],[50,70],[50,50]]",
            "penup",
            "moveto 100 100", // Move to a clear area
            "pendown",
            "draw_square",    // Execute our defined square command
            "go_home"         // Execute our defined home command
        )
        var errorFree = true
        for (command in commands) {
            try {
                val commandRequest = PlotServiceOuterClass.CommandRequest.newBuilder()
                    .setCommand(command)
                    .build()
                val commandResponse = stub.processCommand(commandRequest)
                if (!commandResponse.success) {
                    errorFree = false
                    logger.severe("Error processing command '$command'")
                }
                logger.info("Command: $command -> Response: ${commandResponse.message}")
            } catch (e: Exception) {
                logger.severe("Error processing command '$command': ${e.message}")
                fail("Failed to process command '$command'")
            }
            assertTrue(errorFree, "One or more commands failed")
        }

    }

    @Test
    fun `40 test plotting alignment SVG`() {
        val stub = PlotServiceGrpc.newBlockingStub(channel)

        val plotSvgResponse = stub.plotAlignmentSVG(PlotServiceOuterClass.PlotAlignmentSVGRequest.newBuilder().build())
        logger.info("Plotting alignment SVG: ${plotSvgResponse.message}")
        assertTrue(plotSvgResponse.success, "Failed to plot alignment SVG")

    }

    @Test
    fun `50 test walking home position`() {
        val stub = PlotServiceGrpc.newBlockingStub(channel)

        var errorFree = true

        val distance = 0.1f
        for (i in 1..5) {
            errorFree = if (testWalkHome(stub,"x", distance)) errorFree else false
            errorFree = if (testWalkHome(stub,"y", distance)) errorFree else false
        }
        for (i in 1..5) {
            errorFree = if (testWalkHome(stub,"x", -distance)) errorFree else false
            errorFree = if (testWalkHome(stub,"y", -distance)) errorFree else false
        }
        assertTrue(errorFree, "A walk command failed")
    }

    private fun testWalkHome(stub: PlotServiceGrpc.PlotServiceBlockingStub, axis: String, distance: Float): Boolean {
        try {
            val walkHomeRequest = PlotServiceOuterClass.WalkHomeRequest.newBuilder()
                .setAxis(axis)
                .setDistance(distance) // Walk a small distance
                .build()

            val walkHomeResponse = stub.walkHome(walkHomeRequest)
            logger.info("Walking home position in $axis axis: ${walkHomeResponse.message}")
            return walkHomeResponse.success
        } catch (e: Exception) {
            logger.severe("Error walking home position in $axis axis: ${e.message}")
            fail("Failed to walk home position in $axis axis")
        }
    }

    @Test
    fun `60 test resetting home position`() {
        val stub = PlotServiceGrpc.newBlockingStub(channel)
        val resetHomeResponse = stub.resetHomePosition(PlotServiceOuterClass.ResetHomePositionRequest.newBuilder().build())
        logger.info("Resetting home position: ${resetHomeResponse.message}")
        assertTrue(resetHomeResponse.success, "Failed to reset home position")
    }

    @Test
    fun `70 disconnect plotter`() {
        val stub = PlotServiceGrpc.newBlockingStub(channel)

        val disconnectResponse = stub.disconnect(PlotServiceOuterClass.DisconnectRequest.newBuilder().build())
        logger.info("Disconnecting from plotter: ${disconnectResponse.message}")
        assertTrue(disconnectResponse.success, "Failed to disconnect from plotter")
    }

}
