from dataclasses import dataclass
from enum import Enum


class OpCode(Enum):
  CoefficientElementwise = 3
  Ntt = 4
  Intt = 5
  KskInnerProduct = 6
  BaseConv = 7
  Automorph = 8
  Decompose = 9
  ModUp = 10
  ModDown = 11


@dataclass
class Operation():
  opcode: OpCode


@dataclass
class CoefficientElementwise(Operation):
  num_limbs: int
  level: int
