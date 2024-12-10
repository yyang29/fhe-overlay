from .. import data_types


def func(a: data_types.Ciphertext) -> data_types.Ciphertext:
  b = Rescale(a)

  return b
