from .. import data_types


def func(a: data_types.Ciphertext, distance: int) -> data_types.Ciphertext:
  # Currently the API only supports constant `distance`.
  b = RotateLeft(a, 4)

  return b
