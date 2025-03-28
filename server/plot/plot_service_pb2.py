# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: plot_service.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'plot_service.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x12plot_service.proto\x12\x04plot\"\x13\n\x11\x44isconnectRequest\"\x11\n\x0fHasPowerRequest\"%\n\x10HasPowerResponse\x12\x11\n\thas_power\x18\x01 \x01(\x08\"!\n\x0e\x43ommandRequest\x12\x0f\n\x07\x63ommand\x18\x01 \x01(\t\"3\n\x0f\x43ommandResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"=\n\x15InitializePlotRequest\x12\x0f\n\x07options\x18\x01 \x03(\t\x12\x13\n\x0b\x64\x65\x66initions\x18\x02 \x03(\t\"\x19\n\x17PlotAlignmentSVGRequest\"1\n\x0fWalkHomeRequest\x12\x0c\n\x04\x61xis\x18\x01 \x01(\t\x12\x10\n\x08\x64istance\x18\x02 \x01(\x02\"\x1a\n\x18ResetHomePositionRequest\"\"\n RestoreInteractiveContextRequest\"\x1e\n\x1c\x45ndInteractiveContextRequest2\x9d\x05\n\x0bPlotService\x12\x46\n\x0eInitializePlot\x12\x1b.plot.InitializePlotRequest\x1a\x15.plot.CommandResponse\"\x00\x12?\n\x0eProcessCommand\x12\x14.plot.CommandRequest\x1a\x15.plot.CommandResponse\"\x00\x12>\n\nDisconnect\x12\x17.plot.DisconnectRequest\x1a\x15.plot.CommandResponse\"\x00\x12;\n\x08HasPower\x12\x15.plot.HasPowerRequest\x1a\x16.plot.HasPowerResponse\"\x00\x12J\n\x10PlotAlignmentSVG\x12\x1d.plot.PlotAlignmentSVGRequest\x1a\x15.plot.CommandResponse\"\x00\x12:\n\x08WalkHome\x12\x15.plot.WalkHomeRequest\x1a\x15.plot.CommandResponse\"\x00\x12L\n\x11ResetHomePosition\x12\x1e.plot.ResetHomePositionRequest\x1a\x15.plot.CommandResponse\"\x00\x12\\\n\x19RestoreInteractiveContext\x12&.plot.RestoreInteractiveContextRequest\x1a\x15.plot.CommandResponse\"\x00\x12T\n\x15\x45ndInteractiveContext\x12\".plot.EndInteractiveContextRequest\x1a\x15.plot.CommandResponse\"\x00\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'plot_service_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_DISCONNECTREQUEST']._serialized_start=28
  _globals['_DISCONNECTREQUEST']._serialized_end=47
  _globals['_HASPOWERREQUEST']._serialized_start=49
  _globals['_HASPOWERREQUEST']._serialized_end=66
  _globals['_HASPOWERRESPONSE']._serialized_start=68
  _globals['_HASPOWERRESPONSE']._serialized_end=105
  _globals['_COMMANDREQUEST']._serialized_start=107
  _globals['_COMMANDREQUEST']._serialized_end=140
  _globals['_COMMANDRESPONSE']._serialized_start=142
  _globals['_COMMANDRESPONSE']._serialized_end=193
  _globals['_INITIALIZEPLOTREQUEST']._serialized_start=195
  _globals['_INITIALIZEPLOTREQUEST']._serialized_end=256
  _globals['_PLOTALIGNMENTSVGREQUEST']._serialized_start=258
  _globals['_PLOTALIGNMENTSVGREQUEST']._serialized_end=283
  _globals['_WALKHOMEREQUEST']._serialized_start=285
  _globals['_WALKHOMEREQUEST']._serialized_end=334
  _globals['_RESETHOMEPOSITIONREQUEST']._serialized_start=336
  _globals['_RESETHOMEPOSITIONREQUEST']._serialized_end=362
  _globals['_RESTOREINTERACTIVECONTEXTREQUEST']._serialized_start=364
  _globals['_RESTOREINTERACTIVECONTEXTREQUEST']._serialized_end=398
  _globals['_ENDINTERACTIVECONTEXTREQUEST']._serialized_start=400
  _globals['_ENDINTERACTIVECONTEXTREQUEST']._serialized_end=430
  _globals['_PLOTSERVICE']._serialized_start=433
  _globals['_PLOTSERVICE']._serialized_end=1102
# @@protoc_insertion_point(module_scope)
