from dataclasses import dataclass
from enum import Enum, auto


class OpCode(Enum):
  DmaRead = "DMA_READ"
  DmaWrite = "DMA_WRITE"
  ModAdd = "MOD_ADD"
  ModSub = "MOD_SUB"
  ModMul = "MOD_MUL"
  Butterfly = "BUTTERFLY"
  Barrier = "BARRIER"
  Permute = "PERMUTE"


class FunctionUnit(Enum):
  DmaRead = auto()
  DmaWrite = auto()
  ComputeArray = auto()
  Permute = auto()


@dataclass
class Instruction():
  opcode: OpCode
  sync: list[int]
  wait: int


@dataclass
class DmaRead(Instruction):
  src: int
  dst: int
  size_bytes: int


@dataclass
class DmaWrite(Instruction):
  src: int
  dst: int
  size_bytes: int
