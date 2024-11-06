import logging
import networkx as nx
import matplotlib.pyplot as plt

from compiler import data_types
from compiler import ir
from compiler import isa


class InstructionGeneration():
  """Lower the DAG of HE operations to ISA."""

  def __init__(self, he_params):
    # The backend passes apply optimizations to the IR DAG (apply_optimization
    # = True).
    # First, we rewrite the graph by removing Split and Merge nodes. If a Merge
    # node is followed by a Split node, we can remove both nodes from the
    # graph. Else, we keep them and consider them as a memory-to-memory copy.
    # Next, we annotate the nodes with dataflow types and add a node group
    # to each node. We use BFS, start with the first node and add its children
    # to the same group as long as they have the same dataflow type. We then
    # change the memory location hint for all the internal nodes to SRAM.
    # Finally, we apply a hierarchical topological sort to determine the
    # execution order of the nodes.
    # Finally, we generate the ISA code for the nodes in the graph.
    self._he_params = he_params
    self._instructions = []

  def transform(self, dag, apply_optimization):
    if apply_optimization:
      # Remove Split and Merge nodes.
      dag = self._remove_merge_split_pairs(dag)
      labels = {}
      for node, data in dag.nodes(data=True):
        label = data.get('ir_op', '')
        if label == '':
          labels[node] = node if data.get('op') is None else data.get('op')
        else:
          labels[node] = str(label)
      plt.figure(figsize=(18, 16))
      nx.draw(dag,
              with_labels=True,
              labels=labels,
              node_color='skyblue',
              node_size=500,
              font_size=15,
              font_color='black',
              edge_color='gray')
      plt.savefig("backend_graph.png", format="PNG")

      # Annotate nodes with node groups.

      # Produce instruction sequences based on hierarchical topological sort.

    else:
      topological_order = list(nx.topological_sort(dag))
      logging.info("Topological Sort Order with Node Data:")
      for node in topological_order:
        print(f"{node}: {dag.nodes[node]}")
        self._instructions.append(dag.nodes[node])

    return self._instructions

  def _remove_merge_split_pairs(self, graph):
    nodes = list(graph.nodes)
    for node in nodes:
      if node is not None:
        # Check if the node is a 'merge' node
        logging.info(f"Node: {node} {graph.nodes[node].get('ir_op')}")
        if (graph.nodes[node].get('ir_op') is not None and
            graph.nodes[node].get('ir_op').opcode == ir.OpCode.Merge):
          successors = list(graph.successors(node))

          # Check if the successor is a 'split' node
          if (len(successors) == 1 and
              graph.nodes[successors[0]].get('ir_op').opcode
              == ir.OpCode.Split):
            split_node = successors[0]
            nodes.remove(split_node)

            # Get predecessors of the merge node and successors of the split node
            merge_predecessors = list(graph.predecessors(node))
            split_successors = list(graph.successors(split_node))

            # Remove merge and split nodes
            graph.remove_node(node)
            graph.remove_node(split_node)

            # Connect each predecessor of merge to each successor of split
            for pred in merge_predecessors:
              for succ in split_successors:
                graph.add_edge(pred, succ)

    return graph
