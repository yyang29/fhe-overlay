from dataclasses import dataclass
from enum import Enum, auto

from compiler import data_types


class MemoryLocation(Enum):
  Ddr = auto()
  Scratchpad = auto()


class OpCode(Enum):
  LimbElementwise = auto()
  Ntt = auto()
  KskInnerProduct = auto()
  Automorph = auto()
  Decompose = auto()
  BaseConv = auto()
  Merge = auto()
  Split = auto()


class LimbElementwiseOpCode(Enum):
  Add = 0
  Sub = 1
  Mul = 2


class NttOpCode(Enum):
  Forward = 0
  Inverse = 1


@dataclass(kw_only=True)
class Operation():
  opcode: OpCode
  input_location: MemoryLocation = MemoryLocation.Ddr
  output_location: MemoryLocation = MemoryLocation.Ddr


@dataclass(kw_only=True)
class LimbElementwise(Operation):
  elementwise_opcode: LimbElementwiseOpCode
  operand1: data_types.LimbVector
  operand2: data_types.LimbVector
  result: data_types.LimbVector


@dataclass(kw_only=True)
class Ntt(Operation):
  ntt_opcode: NttOpCode
  operand: data_types.LimbVector
  result: data_types.LimbVector


@dataclass(kw_only=True)
class KskInnerProduct(Operation):
  operand1: data_types.LimbMatrix
  operand2: data_types.LimbVector
  result: data_types.LimbVector


@dataclass(kw_only=True)
class Automorph(Operation):
  operand: data_types.LimbVector
  distance: data_types.Scalar
  result: data_types.LimbVector


@dataclass(kw_only=True)
class Decompose(Operation):
  operand: data_types.LimbVector
  result: data_types.LimbVector


@dataclass(kw_only=True)
class BaseConv(Operation):
  operand: data_types.LimbVector
  result: data_types.LimbVector


@dataclass(kw_only=True)
class Merge(Operation):
  operand1: data_types.LimbVector
  operand2: data_types.LimbVector
  result: data_types.LimbMatrix


@dataclass(kw_only=True)
class Split(Operation):
  operand: data_types.LimbMatrix
  result1: data_types.LimbVector
  result2: data_types.LimbVector
