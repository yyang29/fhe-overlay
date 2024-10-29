import logging
import networkx as nx


class SubroutineLowering():
  """Lower the DAG of HE operations to IR."""

  def __init__(self):
    self._dag = None
    self._ir_dag = nx.DiGraph()

  def transform(self, dag):
    self._dag = dag

    for node in list(dag.nodes):  # Iterate over a list of original nodes
      op_type = dag.nodes[node].get('op')

      if op_type == 'CtCtAdd':
        self._transform_ctct_add(node)

    return self._ir_dag

  def _transform_ctct_add(self, node):
    precedents = list(self._dag.predecessors(node))
    logging.info(f"Debug -- precedents: {precedents}")
    # Create new subnodes: Split, Elementwise1, Elementwise2, Concat
    # split_node = f"{node}_Split"
    # elementwise1_node = f"{node}_Elementwise1"
    # elementwise2_node = f"{node}_Elementwise2"
    # concat_node = f"{node}_Concat"

    # # Add these new nodes to the graph
    # new_graph.add_node(split_node, op="Split")
    # new_graph.add_node(elementwise1_node, op="Elementwise")
    # new_graph.add_node(elementwise2_node, op="Elementwise")
    # new_graph.add_node(concat_node, op="Concat")

    # # Connect the new nodes in sequence
    # new_graph.add_edge(split_node, elementwise1_node)
    # new_graph.add_edge(split_node, elementwise2_node)
    # new_graph.add_edge(elementwise1_node, concat_node)
    # new_graph.add_edge(elementwise2_node, concat_node)

    # # Transfer the incoming edges to the Split node
    # new_graph.add_edge(left_input, split_node)
    # new_graph.add_edge(right_input, split_node)

    # # Transfer the outgoing edges from the HeAdd node to the Concat node
    # for successor in graph.successors(node):
    #   new_graph.add_edge(concat_node, successor)

  def _transform_ctct_sub(self, node):
    pass

  def _transform_ctct_mul(self, node):
    pass
