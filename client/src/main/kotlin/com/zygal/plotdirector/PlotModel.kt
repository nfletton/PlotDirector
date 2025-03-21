package com.zygal.plotdirector

import io.grpc.ManagedChannel
import io.grpc.ManagedChannelBuilder
import java.io.File


//private var channel: ManagedChannel
//init {
//    channel = ManagedChannelBuilder
//        .forAddress("localhost", 50051)
//        .usePlaintext()
//        .build()
//    logger.info("Channel created")
//}


enum class PlotSection {
    OPTIONS, DEFINITIONS, COMMANDS
}

class PlotData(val plotFilePath: String) {

    val options: List<String>
    val definitions: List<String>
    private var commands: MutableList<String>

    init {
        val (opt, def, cmd) = loadFile()
        options = opt
        definitions = def
        commands = cmd.toMutableList()
    }

    fun nextCommand(): String? {
        return commands.removeFirst().takeIf { it.isNotEmpty() }
    }

    private fun loadFile(): Triple<List<String>, List<String>, List<String>> {
        val options = mutableListOf<String>()
        val definitions = mutableListOf<String>()
        val commands = mutableListOf<String>()

        val sectionMapping = mapOf(
            "::END_OPTIONS::" to PlotSection.DEFINITIONS,
            "::END_DEFINITIONS::" to PlotSection.COMMANDS
        )

        var section = PlotSection.OPTIONS

        File(plotFilePath).forEachLine { line ->
            val trimmed = line.trim()
            if (trimmed.isEmpty()) return@forEachLine

            if (trimmed.startsWith("::END_")) {
                section = sectionMapping[trimmed] ?: section
            } else {
                when (section) {
                    PlotSection.OPTIONS -> options.add(trimmed)
                    PlotSection.DEFINITIONS -> definitions.add(trimmed)
                    PlotSection.COMMANDS -> commands.add(trimmed)
                }
            }
        }
        return Triple(options, definitions, commands)
    }

}
