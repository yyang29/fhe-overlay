import logging
import networkx as nx

from compiler import data_types
from compiler import ir


class SubroutineLowering():
  """Lower the DAG of HE operations to IR."""

  def __init__(self, he_params):
    self._he_params = he_params
    self._ir_dag = nx.DiGraph()

  def transform(self, dag):
    self._ir_dag = dag

    for node in list(dag.nodes):  # Iterate over a list of original nodes
      op_type = dag.nodes[node].get('op', '')

      if op_type in ['CtCtAdd', 'CtCtSub']:
        self._transform_ctct_add_sub(node)
      elif op_type in ['PtCtAdd', 'PtCtSub']:
        self._transform_ptct_add_sub(node)
      elif op_type == 'CtCtMult':
        self._transform_ctct_mul(node)
      elif op_type == 'PtCtMult':
        # Use Rescale as a proxy for now.
        self._transform_rescale(node)
      elif 'Rotate' in op_type:
        self._transform_rotate(node)
      elif op_type == 'Rescale':
        self._transform_rescale(node)
      elif op_type == 'Bootstrap':
        pass
      elif op_type == '':
        dag.nodes[node]['ir_op'] = ir.Operation(opcode=ir.OpCode.NoOp)

    return self._ir_dag

  def _transform_ctct_add_sub(self, node):
    attrs = self._ir_dag.nodes[node]
    num_input_limbs = attrs.get('num_input_limbs')
    limb = data_types.Limb(self._he_params.N)

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

  def _transform_ptct_add_sub(self, node):
    attrs = self._ir_dag.nodes[node]
    num_input_limbs = attrs.get('num_input_limbs')
    limb = data_types.Limb(self._he_params.N)

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
    split_node = f"{node}_split"
    elementwise1 = f"{node}_elementwise1"
    elementwise2 = f"{node}_elementwise2"
    merge_node = f"{node}_merge"

    # Add new nodes with respective attributes
    self._ir_dag.add_node(split_node, ir_op=split_op)
    self._ir_dag.add_node(elementwise1, ir_op=elementwise_op)
    self._ir_dag.add_node(elementwise2, ir_op=elementwise_op)
    self._ir_dag.add_node(merge_node, ir_op=merge_op)

    # Redirect edges
    # 1. Connect predecessors of the original node to the split node
    predecessors = list(self._ir_dag.predecessors(node))
    self._ir_dag.add_edge(predecessors[0], split_node)
    for pred in predecessors:
      self._ir_dag.remove_edge(pred, node)

    # 2. Connect split node to the two element-wise add nodes
    self._ir_dag.add_edge(split_node, elementwise1)
    self._ir_dag.add_edge(split_node, elementwise2)
    self._ir_dag.add_edge(predecessors[1], elementwise1)
    self._ir_dag.add_edge(predecessors[1], elementwise2)

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

  def _transform_ctct_mul(self, node):
    attrs = self._ir_dag.nodes[node]
    num_input_limbs = attrs.get('num_input_limbs')
    num_output_limbs = attrs.get('num_output_limbs')
    self._he_params.l = num_input_limbs
    limb = data_types.Limb(self._he_params.N)
    input_limb_matrix = data_types.LimbMatrix(limb, 2, num_input_limbs)
    input_limb_vector = data_types.LimbVector(limb, num_input_limbs)
    output_limb_matrix = data_types.LimbMatrix(limb, 2, num_output_limbs)
    output_limb_vector = data_types.LimbVector(limb, num_output_limbs)
    decomposed_limb_matrix = data_types.LimbMatrix(limb, self._he_params.beta,
                                                   self._he_params.alpha)
    decomposed_limb_vector = data_types.LimbVector(limb, self._he_params.alpha)
    mod_up_limb_vector = data_types.LimbVector(
        limb, self._he_params.alpha * self._he_params.beta +
        self._he_params.log_P - 1)
    ksk_output_limb_matrix_full = data_types.LimbMatrix(
        limb, 2, self._he_params.alpha * self._he_params.beta +
        self._he_params.log_P - 1)

    split_op = ir.Split(opcode=ir.OpCode.Split,
                        operand=input_limb_matrix,
                        result1=input_limb_vector,
                        result2=input_limb_vector)
    split1_node = f"{node}_split1"
    self._ir_dag.add_node(split1_node, ir_op=split_op)
    split2_node = f"{node}_split2"
    self._ir_dag.add_node(split2_node, ir_op=split_op)

    # 1. Connect predecessors of the original node to the split node
    predecessors = list(self._ir_dag.predecessors(node))
    assert len(predecessors) == 2
    self._ir_dag.add_edge(predecessors[0], split1_node)
    self._ir_dag.add_edge(predecessors[1], split2_node)
    for pred in predecessors:
      self._ir_dag.remove_edge(pred, node)

    elementwise_op = ir.LimbElementwise(
        opcode=ir.OpCode.LimbElementwise,
        elementwise_opcode=ir.LimbElementwiseOpCode.Mul,
        operand1=input_limb_vector,
        operand2=input_limb_vector,
        result=input_limb_vector)
    elementwise_nodes = []
    for i in range(0, 5):
      elementwise_nodes.append(f"{node}_elementwise{i}")
      self._ir_dag.add_node(elementwise_nodes[i], ir_op=elementwise_op)

    self._ir_dag.add_edge(split1_node, elementwise_nodes[0])
    self._ir_dag.add_edge(split1_node, elementwise_nodes[1])
    self._ir_dag.add_edge(split1_node, elementwise_nodes[2])
    self._ir_dag.add_edge(split1_node, elementwise_nodes[3])
    self._ir_dag.add_edge(split2_node, elementwise_nodes[0])
    self._ir_dag.add_edge(split2_node, elementwise_nodes[1])
    self._ir_dag.add_edge(split2_node, elementwise_nodes[2])
    self._ir_dag.add_edge(split2_node, elementwise_nodes[3])
    self._ir_dag.add_edge(elementwise_nodes[1], elementwise_nodes[4])
    self._ir_dag.add_edge(elementwise_nodes[2], elementwise_nodes[4])

    decompose_op = ir.Decompose(opcode=ir.OpCode.Decompose,
                                operand=input_limb_vector,
                                result=decomposed_limb_matrix)
    decompose_node = f"{node}_decompose"
    self._ir_dag.add_node(decompose_node, ir_op=decompose_op)
    self._ir_dag.add_edge(elementwise_nodes[0], decompose_node)

    decompose_split_op = ir.Split(opcode=ir.OpCode.Split,
                                  operand=decomposed_limb_matrix,
                                  result1=decomposed_limb_vector,
                                  result2=decomposed_limb_vector)
    decompose_split_node = f"{node}_decompose_split"
    self._ir_dag.add_node(decompose_split_node, ir_op=decompose_split_op)
    self._ir_dag.add_edge(decompose_node, decompose_split_node)

    mod_up_op = ir.BaseConv(opcode=ir.OpCode.BaseConv,
                            dataflow=ir.DataflowType.Coefficient,
                            operand=decomposed_limb_vector,
                            result=mod_up_limb_vector)
    mod_up_nodes = []
    for i in range(0, self._he_params.beta):
      mod_up_nodes.append(f"{node}_mod_up_{i}")
      self._ir_dag.add_node(mod_up_nodes[i], ir_op=mod_up_op)
      self._ir_dag.add_edge(decompose_split_node, mod_up_nodes[i])

    ksk_limb_matrix = data_types.LimbMatrix(limb, 1, self._he_params.beta)
    ksk = data_types.LimbMatrix(limb, self._he_params.beta, 2)
    ksk_output_limb_matrix = data_types.LimbMatrix(limb, 1, 2)
    ksk_op = ir.KskInnerProduct(opcode=ir.OpCode.KskInnerProduct,
                                alpha=self._he_params.alpha,
                                operand1=ksk_limb_matrix,
                                operand2=ksk,
                                result=ksk_output_limb_matrix)
    ksk_node = f"{node}_ksk"
    self._ir_dag.add_node(ksk_node, ir_op=ksk_op)
    for i in range(0, self._he_params.beta):
      self._ir_dag.add_edge(mod_up_nodes[i], ksk_node)

    split_op = ir.Split(opcode=ir.OpCode.Split,
                        operand=ksk_output_limb_matrix_full,
                        result1=mod_up_limb_vector,
                        result2=mod_up_limb_vector)
    split_node = f"{node}_ksk_output_split"
    self._ir_dag.add_node(split_node, ir_op=split_op)
    self._ir_dag.add_edge(ksk_node, split_node)

    mod_down_op = ir.BaseConv(opcode=ir.OpCode.BaseConv,
                              dataflow=ir.DataflowType.Coefficient,
                              operand=mod_up_limb_vector,
                              result=output_limb_vector)
    mod_down_nodes = []
    for i in range(0, 2):
      mod_down_nodes.append(f"{node}_mod_down_{i}")
      self._ir_dag.add_node(mod_down_nodes[i], ir_op=mod_down_op)
      self._ir_dag.add_edge(split_node, mod_down_nodes[i])

    final_elementwise_op = ir.LimbElementwise(
        opcode=ir.OpCode.LimbElementwise,
        elementwise_opcode=ir.LimbElementwiseOpCode.Add,
        operand1=output_limb_vector,
        operand2=output_limb_vector,
        result=output_limb_vector)
    final_add_nodes = []
    for i in range(0, 2):
      final_add_nodes.append(f"{node}_final_add_{i}")
      self._ir_dag.add_node(final_add_nodes[i], ir_op=final_elementwise_op)
      self._ir_dag.add_edge(mod_down_nodes[i], final_add_nodes[i])

    final_merge_op = ir.Merge(opcode=ir.OpCode.Merge,
                              operand1=output_limb_vector,
                              operand2=output_limb_vector,
                              result=output_limb_matrix)
    final_merge_node = f"{node}_final_merge"
    self._ir_dag.add_node(final_merge_node, ir_op=final_merge_op)
    self._ir_dag.add_edge(final_add_nodes[0], final_merge_node)
    self._ir_dag.add_edge(final_add_nodes[1], final_merge_node)

    # 4. Connect the merge node to the original node's successors
    successors = list(self._ir_dag.successors(node))
    for succ in successors:
      self._ir_dag.add_edge(final_merge_node, succ)
      self._ir_dag.remove_edge(node, succ)

    # Finally, remove the original CtCtAdd node
    self._ir_dag.remove_node(node)

  def _transform_rescale(self, node):
    attrs = self._ir_dag.nodes[node]
    num_input_limbs = attrs.get('num_input_limbs')
    num_output_limbs = attrs.get('num_output_limbs')
    limb = data_types.Limb(self._he_params.N)

    input_limb_matrix = data_types.LimbMatrix(limb, 2, num_input_limbs)
    input_limb_vector = data_types.LimbVector(limb, num_input_limbs)
    output_limb_vector = data_types.LimbVector(limb, num_output_limbs)
    output_limb_matrix = data_types.LimbMatrix(limb, 2, num_output_limbs)

    split_op = ir.Split(opcode=ir.OpCode.Split,
                        operand=input_limb_matrix,
                        result1=input_limb_vector,
                        result2=input_limb_vector)
    base_conv_op = ir.BaseConv(opcode=ir.OpCode.BaseConv,
                               dataflow=ir.DataflowType.Coefficient,
                               operand=input_limb_vector,
                               result=output_limb_vector)
    merge_op = ir.Merge(opcode=ir.OpCode.Merge,
                        operand1=output_limb_vector,
                        operand2=output_limb_vector,
                        result=output_limb_matrix)

    # Define new nodes
    split_node = f"{node}_split"
    base_conv1_node = f"{node}_base_conv1"
    base_conv2_node = f"{node}_base_conv2"
    merge_node = f"{node}_merge"

    # Add new nodes with respective attributes
    self._ir_dag.add_node(split_node, ir_op=split_op)
    self._ir_dag.add_node(base_conv1_node, ir_op=base_conv_op)
    self._ir_dag.add_node(base_conv2_node, ir_op=base_conv_op)
    self._ir_dag.add_node(merge_node, ir_op=merge_op)

    # Redirect edges
    # 1. Connect predecessors of the original node to the split node
    predecessors = list(self._ir_dag.predecessors(node))
    assert len(predecessors) == 1
    self._ir_dag.add_edge(predecessors[0], split_node)
    self._ir_dag.remove_edge(predecessors[0], node)

    # 2. Connect split node to the two element-wise add nodes
    self._ir_dag.add_edge(split_node, base_conv1_node)
    self._ir_dag.add_edge(split_node, base_conv2_node)

    # 3. Connect element-wise add nodes to the merge node
    self._ir_dag.add_edge(base_conv1_node, merge_node)
    self._ir_dag.add_edge(base_conv2_node, merge_node)

    # 4. Connect the merge node to the original node's successors
    successors = list(self._ir_dag.successors(node))
    for succ in successors:
      self._ir_dag.add_edge(merge_node, succ)
      self._ir_dag.remove_edge(node, succ)

    # Finally, remove the original CtCtAdd node
    self._ir_dag.remove_node(node)

  def _transform_rotate(self, node):
    # TODO: Rotate should require less ops compared to CtCtMult.
    attrs = self._ir_dag.nodes[node]
    num_input_limbs = attrs.get('num_input_limbs')
    num_output_limbs = attrs.get('num_output_limbs')
    self._he_params.l = num_input_limbs
    limb = data_types.Limb(self._he_params.N)
    input_limb_matrix = data_types.LimbMatrix(limb, 2, num_input_limbs)
    input_limb_vector = data_types.LimbVector(limb, num_input_limbs)
    output_limb_matrix = data_types.LimbMatrix(limb, 2, num_output_limbs)
    output_limb_vector = data_types.LimbVector(limb, num_output_limbs)
    decomposed_limb_matrix = data_types.LimbMatrix(limb, self._he_params.beta,
                                                   self._he_params.alpha)
    decomposed_limb_vector = data_types.LimbVector(limb, self._he_params.alpha)
    mod_up_limb_vector = data_types.LimbVector(
        limb, self._he_params.alpha * self._he_params.beta +
        self._he_params.log_P - 1)
    ksk_output_limb_matrix_full = data_types.LimbMatrix(
        limb, 2, self._he_params.alpha * self._he_params.beta +
        self._he_params.log_P - 1)

    split_op = ir.Split(opcode=ir.OpCode.Split,
                        operand=input_limb_matrix,
                        result1=input_limb_vector,
                        result2=input_limb_vector)
    split1_node = f"{node}_split1"
    self._ir_dag.add_node(split1_node, ir_op=split_op)
    split2_node = f"{node}_split2"
    self._ir_dag.add_node(split2_node, ir_op=split_op)

    # 1. Connect predecessors of the original node to the split node
    predecessors = list(self._ir_dag.predecessors(node))
    assert len(predecessors) == 2
    self._ir_dag.add_edge(predecessors[0], split1_node)
    self._ir_dag.add_edge(predecessors[1], split2_node)
    for pred in predecessors:
      self._ir_dag.remove_edge(pred, node)

    elementwise_op = ir.LimbElementwise(
        opcode=ir.OpCode.LimbElementwise,
        elementwise_opcode=ir.LimbElementwiseOpCode.Mul,
        operand1=input_limb_vector,
        operand2=input_limb_vector,
        result=input_limb_vector)
    elementwise_nodes = []
    for i in range(0, 5):
      elementwise_nodes.append(f"{node}_elementwise{i}")
      self._ir_dag.add_node(elementwise_nodes[i], ir_op=elementwise_op)

    self._ir_dag.add_edge(split1_node, elementwise_nodes[0])
    self._ir_dag.add_edge(split1_node, elementwise_nodes[1])
    self._ir_dag.add_edge(split1_node, elementwise_nodes[2])
    self._ir_dag.add_edge(split1_node, elementwise_nodes[3])
    self._ir_dag.add_edge(split2_node, elementwise_nodes[0])
    self._ir_dag.add_edge(split2_node, elementwise_nodes[1])
    self._ir_dag.add_edge(split2_node, elementwise_nodes[2])
    self._ir_dag.add_edge(split2_node, elementwise_nodes[3])
    self._ir_dag.add_edge(elementwise_nodes[1], elementwise_nodes[4])
    self._ir_dag.add_edge(elementwise_nodes[2], elementwise_nodes[4])

    decompose_op = ir.Decompose(opcode=ir.OpCode.Decompose,
                                operand=input_limb_vector,
                                result=decomposed_limb_matrix)
    decompose_node = f"{node}_decompose"
    self._ir_dag.add_node(decompose_node, ir_op=decompose_op)
    self._ir_dag.add_edge(elementwise_nodes[0], decompose_node)

    decompose_split_op = ir.Split(opcode=ir.OpCode.Split,
                                  operand=decomposed_limb_matrix,
                                  result1=decomposed_limb_vector,
                                  result2=decomposed_limb_vector)
    decompose_split_node = f"{node}_decompose_split"
    self._ir_dag.add_node(decompose_split_node, ir_op=decompose_split_op)
    self._ir_dag.add_edge(decompose_node, decompose_split_node)

    mod_up_op = ir.BaseConv(opcode=ir.OpCode.BaseConv,
                            dataflow=ir.DataflowType.Coefficient,
                            operand=decomposed_limb_vector,
                            result=mod_up_limb_vector)
    mod_up_nodes = []
    for i in range(0, self._he_params.beta):
      mod_up_nodes.append(f"{node}_mod_up_{i}")
      self._ir_dag.add_node(mod_up_nodes[i], ir_op=mod_up_op)
      self._ir_dag.add_edge(decompose_split_node, mod_up_nodes[i])

    ksk_limb_matrix = data_types.LimbMatrix(limb, 1, self._he_params.beta)
    ksk = data_types.LimbMatrix(limb, self._he_params.beta, 2)
    ksk_output_limb_matrix = data_types.LimbMatrix(limb, 1, 2)
    ksk_op = ir.KskInnerProduct(opcode=ir.OpCode.KskInnerProduct,
                                alpha=self._he_params.alpha,
                                operand1=ksk_limb_matrix,
                                operand2=ksk,
                                result=ksk_output_limb_matrix)
    ksk_node = f"{node}_ksk"
    self._ir_dag.add_node(ksk_node, ir_op=ksk_op)
    for i in range(0, self._he_params.beta):
      self._ir_dag.add_edge(mod_up_nodes[i], ksk_node)

    split_op = ir.Split(opcode=ir.OpCode.Split,
                        operand=ksk_output_limb_matrix_full,
                        result1=mod_up_limb_vector,
                        result2=mod_up_limb_vector)
    split_node = f"{node}_ksk_output_split"
    self._ir_dag.add_node(split_node, ir_op=split_op)
    self._ir_dag.add_edge(ksk_node, split_node)

    mod_down_op = ir.BaseConv(opcode=ir.OpCode.BaseConv,
                              dataflow=ir.DataflowType.Coefficient,
                              operand=mod_up_limb_vector,
                              result=output_limb_vector)
    mod_down_nodes = []
    for i in range(0, 2):
      mod_down_nodes.append(f"{node}_mod_down_{i}")
      self._ir_dag.add_node(mod_down_nodes[i], ir_op=mod_down_op)
      self._ir_dag.add_edge(split_node, mod_down_nodes[i])

    final_elementwise_op = ir.LimbElementwise(
        opcode=ir.OpCode.LimbElementwise,
        elementwise_opcode=ir.LimbElementwiseOpCode.Add,
        operand1=output_limb_vector,
        operand2=output_limb_vector,
        result=output_limb_vector)
    final_add_nodes = []
    for i in range(0, 2):
      final_add_nodes.append(f"{node}_final_add_{i}")
      self._ir_dag.add_node(final_add_nodes[i], ir_op=final_elementwise_op)
      self._ir_dag.add_edge(mod_down_nodes[i], final_add_nodes[i])

    final_merge_op = ir.Merge(opcode=ir.OpCode.Merge,
                              operand1=output_limb_vector,
                              operand2=output_limb_vector,
                              result=output_limb_matrix)
    final_merge_node = f"{node}_final_merge"
    self._ir_dag.add_node(final_merge_node, ir_op=final_merge_op)
    self._ir_dag.add_edge(final_add_nodes[0], final_merge_node)
    self._ir_dag.add_edge(final_add_nodes[1], final_merge_node)

    # 4. Connect the merge node to the original node's successors
    successors = list(self._ir_dag.successors(node))
    for succ in successors:
      self._ir_dag.add_edge(final_merge_node, succ)
      self._ir_dag.remove_edge(node, succ)

    # Finally, remove the original CtCtAdd node
    self._ir_dag.remove_node(node)
