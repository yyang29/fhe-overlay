import networkx as nx


class SubroutineLowering():
  """Lower the DAG of HE operations to IR."""

  def __init__(self):
    pass

  def transform(self, dag):
    new_graph = nx.DiGraph()

    for node in list(dag.nodes):  # Iterate over a list of original nodes
      op_type = dag.nodes[node].get('op')

      if op_type == 'CtCtAdd':
        # Get the input edges
        left_input = dag.nodes[node].get('left')
        right_input = dag.nodes[node].get('right')

        # Create new subnodes: Split, Elementwise1, Elementwise2, Concat
        split_node = f"{node}_Split"
        elementwise1_node = f"{node}_Elementwise1"
        elementwise2_node = f"{node}_Elementwise2"
        concat_node = f"{node}_Concat"

        # Add these new nodes to the graph
        new_graph.add_node(split_node, op="Split")
        new_graph.add_node(elementwise1_node, op="Elementwise")
        new_graph.add_node(elementwise2_node, op="Elementwise")
        new_graph.add_node(concat_node, op="Concat")

        # Connect the new nodes in sequence
        new_graph.add_edge(split_node, elementwise1_node)
        new_graph.add_edge(split_node, elementwise2_node)
        new_graph.add_edge(elementwise1_node, concat_node)
        new_graph.add_edge(elementwise2_node, concat_node)

        # Transfer the incoming edges to the Split node
        new_graph.add_edge(left_input, split_node)
        new_graph.add_edge(right_input, split_node)

        # Transfer the outgoing edges from the HeAdd node to the Concat node
        for successor in graph.successors(node):
          new_graph.add_edge(concat_node, successor)
      else:
        # For other nodes, copy them directly to the new graph
        new_graph.add_node(node, **graph.nodes[node])
        for successor in graph.successors(node):
          new_graph.add_edge(node, successor)

    return new_graph

  def _transform_ctct_add(self, node):
    pass

  def _transform_ctct_sub(self, node):
    pass

  def _transform_ctct_mul(self, node):
    pass


# import networkx as nx

# def lower_to_subroutines(graph):
#     """Transforms each operation node in the graph to its corresponding subroutine nodes."""
#     subroutine_map = {
#         'HeAdd': ['LimbElementwise'],
#         'HeMult': ['LimbElementwise', 'Intt', 'Ntt', 'ModUp', 'ModDown'],
#     }

#     new_graph = nx.DiGraph()  # Create a new graph to store the subroutine-expanded DAG

#     for node in list(graph.nodes):  # Iterate over a list of original nodes
#         op_type = graph.nodes[node].get('op')

#         if op_type in subroutine_map:
#             # Get the subroutine sequence for the operation
#             subroutines = subroutine_map[op_type]

#             # Replace the original node with a sequence of subroutine nodes
#             prev_node = None
#             for i, subroutine in enumerate(subroutines):
#                 subroutine_node = f"{node}_{subroutine}_{i}"  # Create a unique node name
#                 new_graph.add_node(subroutine_node, op=subroutine)

#                 if prev_node:
#                     # Connect the subroutines in sequence
#                     new_graph.add_edge(prev_node, subroutine_node)

#                 prev_node = subroutine_node

#             # Transfer incoming edges from the original node to the first subroutine node
#             for predecessor in graph.predecessors(node):
#                 new_graph.add_edge(predecessor, f"{node}_{subroutines[0]}_0")

#             # Transfer outgoing edges from the original node to the last subroutine node
#             for successor in graph.successors(node):
#                 new_graph.add_edge(f"{node}_{subroutines[-1]}_{len(subroutines) - 1}", successor)
#         else:
#             # For other nodes (e.g., variables), copy them directly to the new graph
#             new_graph.add_node(node, **graph.nodes[node])
#             for successor in graph.successors(node):
#                 new_graph.add_edge(node, successor)

#     return new_graph

# # Example DAG input (pre-built graph)
# G = nx.DiGraph()

# # Add nodes and edges (initially with operation types)
# G.add_node('a', op='variable')
# G.add_node('b', op='variable')
# G.add_node('c', op='HeAdd')   # c = a + b
# G.add_node('d', op='HeMult')  # d = c * a
# G.add_edge('a', 'c')
# G.add_edge('b', 'c')
# G.add_edge('c', 'd')
# G.add_edge('a', 'd')

# # Transform the DAG to include subroutine nodes
# transformed_graph = lower_to_subroutines(G)

# # Print the nodes and edges of the transformed graph
# print("Nodes in the transformed graph:")
# for node, data in transformed_graph.nodes(data=True):
#     print(f"{node}: {data}")

# print("\nEdges in the transformed graph:")
# for edge in transformed_graph.edges():
#     print(edge)
