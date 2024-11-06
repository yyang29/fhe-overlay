import logging
import networkx as nx

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
      # Apply optimizations
      pass
    else:
      topological_order = list(nx.topological_sort(dag))
      logging.info("Topological Sort Order with Node Data:")
      for node in topological_order:
        print(f"{node}: {dag.nodes[node]}")
        self._instructions.append(dag.nodes[node])

    return self._instructions
