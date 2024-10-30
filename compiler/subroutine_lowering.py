import logging
import networkx as nx

from compiler import data_types
from compiler import ir


class SubroutineLowering():
  """Lower the DAG of HE operations to IR."""

  def __init__(self, poly_degree):
    self._poly_degree = poly_degree
    self._ir_dag = nx.DiGraph()

  def transform(self, dag):
    self._ir_dag = dag

    for node in list(dag.nodes):  # Iterate over a list of original nodes
      op_type = dag.nodes[node].get('op')

      if op_type == 'CtCtAdd':
        self._transform_ctct_add(node)

    return self._ir_dag

  def _transform_ctct_add(self, node):
    attrs = self._ir_dag.nodes[node]
    num_input_limbs = attrs.get('num_input_limbs')
    limb = data_types.Limb(self._poly_degree)

    input_limb_matrix = data_types.LimbMatrix(limb, 2, num_input_limbs)
    limb_vector = data_types.LimbVector(limb, num_input_limbs)

    split_op = ir.Split(opcode=ir.OpCode.Split,
                        operand=input_limb_matrix,
                        result1=limb_vector,
                        result2=limb_vector)
    elementwise_op = ir.LimbElementwise(
        opcode=ir.OpCode.LimbElementwise,
        elementwise_opcode=ir.LimbElementwiseOpCode.Add,
        operand1=limb_vector,
        operand2=limb_vector,
        result=limb_vector)
    merge_op = ir.Merge(opcode=ir.OpCode.Merge,
                        operand1=limb_vector,
                        operand2=limb_vector,
                        result=input_limb_matrix)

    # Define new nodes
    split1_node = f"{node}_split1"
    split2_node = f"{node}_split2"
    elementwise1 = f"{node}_elementwise1"
    elementwise2 = f"{node}_elementwise2"
    merge_node = f"{node}_merge"

    # Add new nodes with respective attributes
    self._ir_dag.add_node(split1_node, ir_op=split_op)
    self._ir_dag.add_node(split2_node, ir_op=split_op)
    self._ir_dag.add_node(elementwise1, ir_op=elementwise_op)
    self._ir_dag.add_node(elementwise2, ir_op=elementwise_op)
    self._ir_dag.add_node(merge_node, ir_op=merge_op)

    # Redirect edges
    # 1. Connect predecessors of the original node to the split node
    predecessors = list(self._ir_dag.predecessors(node))
    assert len(predecessors) == 2
    self._ir_dag.add_edge(predecessors[0], split1_node)
    self._ir_dag.add_edge(predecessors[1], split2_node)
    for pred in predecessors:
      self._ir_dag.remove_edge(pred, node)

    # 2. Connect split node to the two element-wise add nodes
    self._ir_dag.add_edge(split1_node, elementwise1)
    self._ir_dag.add_edge(split1_node, elementwise2)
    self._ir_dag.add_edge(split2_node, elementwise1)
    self._ir_dag.add_edge(split2_node, elementwise2)

    # 3. Connect element-wise add nodes to the merge node
    self._ir_dag.add_edge(elementwise1, merge_node)
    self._ir_dag.add_edge(elementwise2, merge_node)

    # 4. Connect the merge node to the original node's successors
    successors = list(self._ir_dag.successors(node))
    for succ in successors:
      self._ir_dag.add_edge(merge_node, succ)
      self._ir_dag.remove_edge(node, succ)

    # Finally, remove the original CtCtAdd node
    self._ir_dag.remove_node(node)

  def _transform_ctct_sub(self, node):
    pass

  def _transform_ctct_mul(self, node):
    pass
