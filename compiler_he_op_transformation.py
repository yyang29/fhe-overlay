import ast
import networkx as nx


# Custom AST Nodes
class CtCtAddNode(ast.AST):
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


class HeOpTransformer(ast.NodeTransformer):

  def visit_Call(self, node):
    func_name = getattr(node.func, 'id', None)

    if func_name == 'CtCtAdd':
      return CtCtAddNode(left=node.args[0], right=node.args[1])

    elif func_name == 'CtCtMult':
      return CtCtMultNode(left=node.args[0], right=node.args[1])

    elif func_name == 'RotateLeft':
      return RotateLeftNode(value=node.args[0], n=node.args[1])

    elif func_name == 'RotateRight':
      return RotateRightNode(value=node.args[0], n=node.args[1])

    elif func_name == 'Rescale':
      return RescaleNode(value=node.args[0])

    # For all other calls, proceed with generic visit
    return self.generic_visit(node)


import ast
import networkx as nx


# Custom AST Nodes
class HeAddNode(ast.AST):
  _fields = ['left', 'right']

  def __init__(self, left, right):
    self.left = left
    self.right = right


class HeMultNode(ast.AST):
  _fields = ['left', 'right']

  def __init__(self, left, right):
    self.left = left
    self.right = right


class HeLeftRotateNode(ast.AST):
  _fields = ['value', 'n']

  def __init__(self, value, n):
    self.value = value
    self.n = n


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
                                left=node.left.id,
                                right=node.right.id)
    # Add edges with metadata
    self.add_edge_with_metadata(node.left.id,
                                self.current_var,
                                level=self.current_level,
                                var='left')
    self.add_edge_with_metadata(node.right.id,
                                self.current_var,
                                level=self.current_level,
                                var='right')

  def visit_CtCtMultNode(self, node):
    # Add node with additional metadata
    self.add_node_with_metadata(node,
                                op_type="CtCtMult",
                                left=node.left.id,
                                right=node.right.id)
    # Add edges with metadata
    self.add_edge_with_metadata(node.left.id,
                                self.current_var,
                                level=self.current_level,
                                var='left')
    self.add_edge_with_metadata(node.right.id,
                                self.current_var,
                                level=self.current_level,
                                var='right')

  def visit_RotateLeftNode(self, node):
    # Add node with additional metadata
    self.add_node_with_metadata(node,
                                op_type="RotateLeft",
                                value=node.value.id,
                                rotate_by=node.n)
    # Add edge with metadata
    self.add_edge_with_metadata(node.value.id,
                                self.current_var,
                                level=self.current_level,
                                var='value',
                                rotate_by=node.n)

  def visit_RotateRightNode(self, node):
    # Add node with additional metadata
    self.add_node_with_metadata(node,
                                op_type="RotateRight",
                                value=node.value.id,
                                rotate_by=node.n)
    # Add edge with metadata
    self.add_edge_with_metadata(node.value.id,
                                self.current_var,
                                level=self.current_level,
                                var='value',
                                rotate_by=node.n)

  def visit_RescaleNode(self, node):
    # Add node with additional metadata
    self.add_node_with_metadata(node, op_type="Rescale", value=node.value.id)
    # Add edge with metadata
    self.add_edge_with_metadata(node.value.id,
                                self.current_var,
                                level=self.current_level,
                                var='value')
