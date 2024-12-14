from .. import data_types


def func(a: data_types.Ciphertext,
         b: data_types.Ciphertext) -> data_types.Ciphertext:
  c = CtCtMult(a, b)

  return c
