from dataclasses import dataclass
from enum import Enum, auto

import data_types


class OpCode(Enum):
  LimbElementwise = auto()
  Ntt = auto()
  KskInnerProduct = auto()
  Automorph = auto()
  Decompose = auto()
  ModUp = auto()
  ModDown = auto()


class LimbElementwiseOpCode(Enum):
  Add = 0
  Sub = 1
  Mul = 2


class NttOpCode(Enum):
  Forward = 0
  Inverse = 1


@dataclass
class Operation():
  opcode: OpCode


@dataclass
class LimbElementwise(Operation):
  elementwise_opcode: LimbElementwiseOpCode
  operand1: data_types.LimbVector
  operand2: data_types.LimbVector
  result: data_types.LimbVector


@dataclass
class Ntt(Operation):
  ntt_opcode: NttOpCode
  operand: data_types.LimbVector
  result: data_types.LimbVector


@dataclass
class KskInnerProduct(Operation):
  operand1: data_types.LimbMatrix
  operand2: data_types.LimbVector
  result: data_types.LimbVector


@dataclass
class Automorph(Operation):
  operand: data_types.LimbVector
  result: data_types.LimbVector


@dataclass
class Decompose(Operation):
  operand: data_types.LimbVector
  result: data_types.LimbVector


@dataclass
class ModUp(Operation):
  operand: data_types.LimbVector
  result: data_types.LimbVector


@dataclass
class ModDown(Operation):
  operand: data_types.LimbVector
  result: data_types.LimbVector
