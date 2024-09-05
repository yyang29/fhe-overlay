from dataclasses import dataclass


@dataclass
class Limb():
  N: int


@dataclass
class LimbArray():
  limb: Limb
  num_limbs: int


@dataclass
class Plaintext():
  limb_array: LimbArray
  level: int

  @property
  def num_limb_arrays(self) -> int:
    return 1


@dataclass
class Ciphertext():
  limb_array: LimbArray
  level: int

  @property
  def num_limb_arrays(self) -> int:
    return 2
