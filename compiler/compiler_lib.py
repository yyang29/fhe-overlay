import ast
import logging
import matplotlib.pyplot as plt
import networkx as nx
from compiler import he_op_transformation
from compiler import subroutine_lowering


class Compiler():

  def __init__(self, test_program: str, assembly_output: str, N: int,
               initial_num_limbs: int):
    self._test_program = test_program
    self._assembly_output = assembly_output
    self._poly_degree = N
    self._initial_num_limbs = initial_num_limbs
    self._he_op_transformer = he_op_transformation.HeOpTransformer()
    self._he_op_dag_builder = he_op_transformation.HeOpDagBuilder()
    self._ir_builder = subroutine_lowering.SubroutineLowering(self._poly_degree)

  def run(self):
    self._frontend_passes()
    self._backend_passes()

  def _frontend_passes(self):
    """Generates IR as the output for frontend."""

    # 1. Generate program AST.
    logging.info("-----------------")
    logging.info("AST construction and annotation:")
    parsed_ast = ast.parse(self._test_program)
    # 2. Transform the AST to add metadata for HE operations.
    transformed_ast = self._he_op_transformer.visit(parsed_ast)
    logging.info(ast.dump(transformed_ast))
    logging.info("-----------------\n")

    # 3. Build a DAG of HE operations and num_limbs.
    logging.info("-----------------")
    self._he_op_dag_builder.visit(transformed_ast)
    dag = self._he_op_dag_builder.graph
    self._he_op_dag_builder.add_num_limbs_attributes(self._initial_num_limbs)

    # Display the nodes and edges in the DAG with metadata
    logging.info("HE Operations DAG construction:")
    logging.info(f"Nodes in the DAG: {dag.nodes(data=True)}")
    logging.info("Edges in the DAG with metadata:")
    for src, dst, metadata in dag.edges(data=True):
      logging.info(f"edge from {src} to {dst} with metadata {metadata}")

    labels = {}
    for node, data in dag.nodes(data=True):
      label = data.get('op', '')
      if label == '':
        labels[node] = node
      else:
        labels[node] = label
    plt.figure(figsize=(18, 16))
    nx.draw(dag,
            with_labels=True,
            labels=labels,
            node_color='skyblue',
            node_size=500,
            font_size=15,
            font_color='black',
            edge_color='gray')
    plt.savefig("he_ops_graph.png", format="PNG")
    logging.info("-----------------\n")

    # 4. Lower the DAG to IR.
    logging.info("-----------------")
    logging.info("IR DAG construction:")
    dag = self._ir_builder.transform(dag)

    logging.info(f"Nodes in the DAG: {dag.nodes(data=True)}")
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
    plt.savefig("ir_graph.png", format="PNG")
    logging.info("-----------------\n")

    # Display the nodes and edges in the DAG with metadata
    # logging.info("-----------------")
    # logging.info(type(dag))
    # logging.info(f"Nodes in the DAG: {dag.nodes(data=True)}")
    # logging.info("Edges in the DAG with metadata:")
    # for edge in dag.edges(data=True):
    #   logging.info(edge)

  def _backend_passes(self):
    # 1. Dataflow selection
    # 2. If fusion is enabled, add node group
    # 3. Apply fusion (if enabled)
    # 4. Topological sort for execution order
    # 5. ISA generation
    pass
