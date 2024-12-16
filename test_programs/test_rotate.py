from .. import data_types


def func(a: data_types.Ciphertext, distance: int) -> data_types.Ciphertext:
  b = RotateLeft(a, distance)

  return b
