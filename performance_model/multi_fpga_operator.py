import dataclasses


@dataclasses.dataclass(kw_only=True)
class Gemm():
  m: int
  n: int
  k: int


@dataclasses.dataclass(kw_only=True)
class Conv():
  m: int
  n: int
  k: int
  c: int
  h: int
  w: int
  kh: int
  kw: int
  stride: int
  pad: int
  dilate: int
  groups: int


@dataclasses.dataclass(kw_only=True)
class Elementwise():
  length: int
