from .. import data_types


def func(a: data_types.Ciphertext,
         b: data_types.Ciphertext) -> data_types.Ciphertext:
  c = CtCtAdd(a, b)
  d = CtCtMult(a, c)
  e = RotateLeft(d, 2)
  f = RotateRight(c, 2)
  g = Rescale(e)
  h = Rescale(f)
  i = CtCtAdd(g, h)
  j = Bootstrap(i)

  return j
