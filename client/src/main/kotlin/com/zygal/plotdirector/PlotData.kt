package com.zygal.plotdirector

import java.io.File


enum class PlotSection {
    OPTIONS, DEFINITIONS, COMMANDS
}

class PlotData(private val plotFilePath: String) {

    val commandCount: Int
    val options: List<String>
    val definitions: List<String>
    private var commands: MutableList<String>

    init {
        val (opt, def, cmd) = loadFile()
        options = opt
        definitions = def
        commands = cmd.toMutableList()
        commandCount = commandCount(cmd)
    }

    fun nextCommand(): String? {
        val command = commands.removeFirst().takeIf { it.isNotEmpty() }
        return command
    }

    fun pushCommand(command: String) {
        commands.addFirst(command)
    }

    private fun commandCount(commands: List<String>) =
        commands.count { !it.startsWith("#")}

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

    fun hasCommands() = commands.isNotEmpty()
}
