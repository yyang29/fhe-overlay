from .. import data_types


def func(a: data_types.Ciphertext,
         b: data_types.Ciphertext) -> data_types.Ciphertext:
  c = CtCtAdd(a, b)
  d = CtCtMult(a, c)

  return d
