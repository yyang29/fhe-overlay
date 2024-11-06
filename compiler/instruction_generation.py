from collections import OrderedDict, defaultdict, deque
import logging
import networkx as nx
import matplotlib.pyplot as plt

from compiler import ir


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

      dag = self._annotate_node_groups(dag)

      # Produce instruction sequences based on hierarchical topological sort.
      # First, node group level topological sort is performed. Then, within
      # each group, a topological sort is performed. All internal nodes within
      # a group have mem hints to SRAM.
      # Step 1: Perform a topological sort of all nodes and collect groups in topological order
      sorted_nodes = list(nx.topological_sort(dag))
      group_order = OrderedDict()
      for node in sorted_nodes:
        group = dag.nodes[node].get('ir_op').node_group
        if group not in group_order:
          group_order[group] = []
        group_order[group].append(node)

      # Step 2: Process each group in topologically sorted order and annotate memory hints
      for group, nodes in group_order.items():
        # Perform topological sort within the group
        subgraph = dag.subgraph(nodes)
        group_topo_order = list(nx.topological_sort(subgraph))

        # Add this group's ordered nodes to the overall hierarchical order
        for node in group_topo_order:
          self._instructions.append(dag.nodes[node])

        # Identify first and last levels of nodes in this group
        levels = {}  # Dictionary to store levels for each node within the group
        for node in group_topo_order:
          if node not in levels:
            levels[node] = 0
          for succ in dag.successors(node):
            if succ in nodes:
              levels[succ] = levels[node] + 1

        max_level = max(levels.values())

        # Update memory hints for internal nodes (not in the first or last level of the group)
        for node, level in levels.items():
          if level > 0 and level < max_level:  # Internal levels
            dag.nodes[node].get(
                'ir_op').input_location = ir.MemoryLocation.Scratchpad
            dag.nodes[node].get(
                'ir_op').output_location = ir.MemoryLocation.Scratchpad
          elif level == max_level:
            dag.nodes[node].get(
                'ir_op').input_location = ir.MemoryLocation.Scratchpad
          elif level == 0:
            dag.nodes[node].get(
                'ir_op').output_location = ir.MemoryLocation.Scratchpad

      labels = {}
      for node, data in dag.nodes(data=True):
        label = data.get('ir_op', '')
        if label != '':
          node_group = label.node_group
        else:
          node_group = ''
        if label == '':
          labels[node] = node if data.get('op') is None else data.get('op')
        else:
          labels[node] = str(label) + ' ' + str(node_group)
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
      for node, data in dag.nodes(data=True):
        logging.info(
            f"Node: {node} {data.get('ir_op').opcode} {data.get('ir_op').node_group} input: {data.get('ir_op').input_location} output: {data.get('ir_op').output_location}"
        )

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

  def _annotate_node_groups(self, graph):
    # Annotate nodes with node groups.
    # This is done by doing a BFS of the graph, and for each node visited, if
    # it's dataflow type is different from its parent, assign to a new group.
    # For nodes at the same BFS level with the same dataflow type should
    # always have the same node group.
    queue = deque()
    root_nodes = [node for node in graph.nodes if graph.in_degree(node) == 0]

    # Initialize group counter and dataflow tracking
    group_counter = 0
    level_dataflow_groups = defaultdict(
        dict)  # {level: {dataflow_type: group_number}}

    # Start BFS from each root node
    for root in root_nodes:
      queue.append((root, 0))  # (node, level)

    # Perform BFS
    while queue:
      current_node, level = queue.popleft()
      current_dataflow = graph.nodes[current_node].get(
          'ir_op').dataflow if current_node not in root_nodes else None
      next_level = level + 1

      # Process each child node
      for successor in graph.successors(current_node):
        successor_dataflow = graph.nodes[successor].get('ir_op').dataflow

        # Determine group for the successor
        if successor_dataflow in level_dataflow_groups[next_level]:
          # If a group already exists for this dataflow type at this level, assign it
          graph.nodes[successor].get(
              'ir_op'
          ).node_group = level_dataflow_groups[next_level][successor_dataflow]
        elif successor_dataflow == current_dataflow:
          graph.nodes[successor].get('ir_op').node_group = group_counter
          level_dataflow_groups[next_level][successor_dataflow] = group_counter
        else:
          # Assign a new group if this dataflow type hasn't been seen at this level
          group_counter += 1
          graph.nodes[successor].get('ir_op').node_group = group_counter
          level_dataflow_groups[next_level][successor_dataflow] = group_counter
          logging.info(
              f"Assigning group {group_counter} to node {successor} at level {next_level}"
          )

        # Add successor to the BFS queue
        queue.append((successor, next_level))

    return graph
