def matrix_vector_mult(
    A: List[Ciphertext],
    x: List[Ciphertext],
):
  n: int = len(A)
  sum: ciphertext = 0
  for i in range(n):
    sum += rotate_left(x, i) * A
  return sum
