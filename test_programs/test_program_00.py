from .. import data_types


def func(a: data_types.Ciphertext,
         b: data_types.Ciphertext) -> data_types.Ciphertext:
  c = he_add(a, b)
  d = he_mult(a, c)
  e = he_rotate_left(d, 2)
  return e
