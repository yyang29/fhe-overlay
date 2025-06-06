from dataclasses import dataclass
from enum import Enum, auto

from compiler import data_types


class MemoryLocation(Enum):
  Dram = auto()
  Scratchpad = auto()


class DataflowType(Enum):
  Limb = auto()  # Row by row
  Coefficient = auto()  # Column by column


class OpCode(Enum):
  LimbElementwise = "Limbelementwise"
  Ntt = "Ntt"
  KskInnerProduct = "KskInnerProduct"
  Automorph = "Automorph"
  Decompose = "Decompose"
  BaseConv = "BaseConv"
  Merge = "Merge"
  Split = "Split"
  NoOp = "NoOp"


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
  input_location: MemoryLocation = MemoryLocation.Dram
  output_location: MemoryLocation = MemoryLocation.Dram
  dataflow: DataflowType = DataflowType.Limb
  node_group: int = 0
  num_fpgas: int = 1

  def __str__(self):
    return f"{self.opcode}"[7:]


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
  alpha: int
  operand1: data_types.LimbMatrix
  operand2: data_types.LimbMatrix
  result: data_types.LimbMatrix


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
