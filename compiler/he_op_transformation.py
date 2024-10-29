import ast
import networkx as nx


# Custom AST Nodes
class PtCtAddNode(ast.AST):
  _fields = ['left', 'right']

  def __init__(self, left, right):
    self.left = left
    self.right = right


class PtCtSubNode(ast.AST):
  _fields = ['left', 'right']

  def __init__(self, left, right):
    self.left = left
    self.right = right


class PtCtMultNode(ast.AST):
  _fields = ['left', 'right']

  def __init__(self, left, right):
    self.left = left
    self.right = right


class CtCtAddNode(ast.AST):
  _fields = ['left', 'right']

  def __init__(self, left, right):
    self.left = left
    self.right = right


class CtCtSubNode(ast.AST):
  _fields = ['left', 'right']

  def __init__(self, left, right):
    self.left = left
    self.right = right


class CtCtMultNode(ast.AST):
  _fields = ['left', 'right']

  def __init__(self, left, right):
    self.left = left
    self.right = right


class RotateLeftNode(ast.AST):
  _fields = ['value', 'n']

  def __init__(self, value, n):
    self.value = value
    self.n = n


class RotateRightNode(ast.AST):
  _fields = ['value', 'n']

  def __init__(self, value, n):
    self.value = value
    self.n = n


class RescaleNode(ast.AST):
  _fields = ['value']

  def __init__(self, value):
    self.value = value


class BootstrapNode(ast.AST):
  _fields = ['value']

  def __init__(self, value):
    self.value = value


class HeOpTransformer(ast.NodeTransformer):

  def visit_Call(self, node):
    func_name = getattr(node.func, 'id', None)

    if func_name == 'CtCtAdd':
      return CtCtAddNode(left=node.args[0], right=node.args[1])

    elif func_name == 'CtCtSub':
      return CtCtSubNode(left=node.args[0], right=node.args[1])

    elif func_name == 'CtCtMult':
      return CtCtMultNode(left=node.args[0], right=node.args[1])

    elif func_name == 'PtCtAdd':
      return PtCtAddNode(left=node.args[0], right=node.args[1])

    elif func_name == 'PtCtSub':
      return PtCtSubNode(left=node.args[0], right=node.args[1])

    elif func_name == 'PtCtMult':
      return PtCtMultNode(left=node.args[0], right=node.args[1])

    elif func_name == 'RotateLeft':
      return RotateLeftNode(value=node.args[0], n=node.args[1])

    elif func_name == 'RotateRight':
      return RotateRightNode(value=node.args[0], n=node.args[1])

    elif func_name == 'Rescale':
      return RescaleNode(value=node.args[0])

    elif func_name == 'Bootstrap':
      return BootstrapNode(value=node.args[0])

    # For all other calls, proceed with generic visit
    return self.generic_visit(node)


# Transformer that generates the DAG
class HeOpDagBuilder(ast.NodeVisitor):

  def __init__(self):
    self.graph = nx.DiGraph()
    self.current_var = None
    self.current_level = 0  # Track level to use as metadata for edges

  def add_node_with_metadata(self, node, op_type, **metadata):
    """ Helper function to add metadata to a node """
    self.graph.add_node(self.current_var, op=op_type, **metadata)

  def add_edge_with_metadata(self, source_var, target_op, **metadata):
    """ Helper function to add an edge with metadata to the graph """
    self.graph.add_edge(source_var, target_op, **metadata)

  def visit_Assign(self, node):
    # Get the target variable name
    self.current_var = node.targets[0].id
    self.current_level += 1  # Increase level as we go deeper
    self.generic_visit(node)
    self.current_var = None
    self.current_level -= 1

  def visit_CtCtAddNode(self, node):
    # Add node with additional metadata (line number, variables involved)
    self.add_node_with_metadata(node,
                                op_type="CtCtAdd",
                                num_input_limbs=0,
                                num_output_limbs=0)
    # Add edges with metadata
    self.add_edge_with_metadata(node.left.id, self.current_var)
    self.add_edge_with_metadata(node.right.id, self.current_var)

  def visit_CtCtSubNode(self, node):
    # Add node with additional metadata
    self.add_node_with_metadata(node,
                                op_type="CtCtSub",
                                num_input_limbs=0,
                                num_output_limbs=0)
    # Add edges with metadata
    self.add_edge_with_metadata(node.left.id, self.current_var)
    self.add_edge_with_metadata(node.right.id, self.current_var)

  def visit_CtCtMultNode(self, node):
    # Add node with additional metadata
    self.add_node_with_metadata(node,
                                op_type="CtCtMult",
                                num_input_limbs=0,
                                num_output_limbs=0)
    # Add edges with metadata
    self.add_edge_with_metadata(node.left.id, self.current_var)
    self.add_edge_with_metadata(node.right.id, self.current_var)

  def visit_PtCtAddNode(self, node):
    # Add node with additional metadata
    self.add_node_with_metadata(node,
                                op_type="PtCtAdd",
                                num_input_limbs=0,
                                num_output_limbs=0)
    # Add edges with metadata
    self.add_edge_with_metadata(node.left.id, self.current_var)
    self.add_edge_with_metadata(node.right.id, self.current_var)

  def visit_PtCtSubNode(self, node):
    # Add node with additional metadata
    self.add_node_with_metadata(node,
                                op_type="PtCtSub",
                                num_input_limbs=0,
                                num_output_limbs=0)
    # Add edges with metadata
    self.add_edge_with_metadata(node.left.id, self.current_var)
    self.add_edge_with_metadata(node.right.id, self.current_var)

  def visit_PtCtMultNode(self, node):
    # Add node with additional metadata
    self.add_node_with_metadata(node,
                                op_type="PtCtMult",
                                num_input_limbs=0,
                                num_output_limbs=0)
    # Add edges with metadata
    self.add_edge_with_metadata(node.left.id, self.current_var)
    self.add_edge_with_metadata(node.right.id, self.current_var)

  def visit_RotateLeftNode(self, node):
    # Add node with additional metadata
    self.add_node_with_metadata(node,
                                op_type="RotateLeft",
                                num_input_limbs=0,
                                num_output_limbs=0,
                                rotate_by=node.n.value)
    # Add edge with metadata
    self.add_edge_with_metadata(node.value.id, self.current_var)

  def visit_RotateRightNode(self, node):
    # Add node with additional metadata
    self.add_node_with_metadata(node,
                                op_type="RotateRight",
                                num_input_limbs=0,
                                num_output_limbs=0,
                                rotate_by=node.n.value)
    # Add edge with metadata
    self.add_edge_with_metadata(node.value.id, self.current_var)

  def visit_RescaleNode(self, node):
    # Add node with additional metadata
    self.add_node_with_metadata(node,
                                op_type="Rescale",
                                num_input_limbs=0,
                                num_output_limbs=0)
    # Add edge with metadata
    self.add_edge_with_metadata(node.value.id, self.current_var)

  def visit_BootstrapNode(self, node):
    # Add node with additional metadata
    self.add_node_with_metadata(node,
                                op_type="Bootstrap",
                                num_input_limbs=0,
                                num_output_limbs=0)
    # Add edge with metadata
    self.add_edge_with_metadata(node.value.id, self.current_var)

  def add_num_limbs_attributes(self, initial_num_limbs):
    # First, find the root nodes (nodes with no incoming edges)
    root_nodes = [n for n in self.graph.nodes if self.graph.in_degree(n) == 0]

    # Initialize num_input_limbs and num_output_limbs for root nodes
    for root in root_nodes:
      self.graph.nodes[root]['num_input_limbs'] = initial_num_limbs
      self.graph.nodes[root]['num_output_limbs'] = initial_num_limbs

    # Perform topological sort to ensure we process nodes in dependency order
    topo_sorted_nodes = list(nx.topological_sort(self.graph))

    # Propagate num_input_limbs and num_output_limbs through the graph
    for node in topo_sorted_nodes:
      # Get the current node's input and output limb values
      num_input_limbs = self.graph.nodes[node].get('num_input_limbs', None)
      if num_input_limbs is None:
        continue  # Skip nodes where num_input_limbs is not set yet

      op_type = self.graph.nodes[node].get('op', None)

      # Update num_output_limbs based on the operation type
      if (op_type == 'CtCtAdd' or op_type == 'PtCtAdd' or
          op_type == 'CtCtSub' or op_type == 'CtCtSub'):
        # For HeAdd: num_output_limbs = num_input_limbs
        self.graph.nodes[node]['num_output_limbs'] = num_input_limbs

      elif (op_type == 'CtCtMult' or op_type == 'PtCtMult' or
            op_type == 'RotateLeft' or op_type == 'RotateRight' or
            op_type == 'Rescale'):
        # For HeMult: num_output_limbs = num_input_limbs - 1
        self.graph.nodes[node]['num_output_limbs'] = num_input_limbs - 1

      elif op_type == 'Bootstrap':
        # For Bootstrap: num_output_limbs = 1
        self.graph.nodes[node][
            'num_output_limbs'] = num_input_limbs + initial_num_limbs

      # Propagate num_output_limbs to the children (successors)
      for child in self.graph.successors(node):
        self.graph.nodes[child]['num_input_limbs'] = self.graph.nodes[node][
            'num_output_limbs']
