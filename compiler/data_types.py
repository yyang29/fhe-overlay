from dataclasses import dataclass


@dataclass
class Limb():
  N: int
  q: int = 0


@dataclass
class LimbVector():
  limb: Limb
  num_limbs: int


@dataclass
class LimbMatrix():
  limb: Limb
  num_rows: int
  num_columns: int


@dataclass
class Plaintext():
  limb_array: LimbVector
  level: int


@dataclass
class Ciphertext():
  limb_array: LimbMatrix
  level: int


@dataclass
class Scalar():
  value: int
