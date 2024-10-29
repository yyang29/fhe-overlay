import ast
import logging
import matplotlib.pyplot as plt
import networkx as nx
from compiler import compiler_he_op_transformation
from compiler import compiler_subroutine_lowering


class Compiler():

  def __init__(self, test_program: str, assembly_output: str,
               initial_num_limbs: int):
    self._test_program = test_program
    self._assembly_output = assembly_output
    self._initial_num_limbs = initial_num_limbs
    self._he_op_transformer = compiler_he_op_transformation.HeOpTransformer()
    self._he_op_dag_builder = compiler_he_op_transformation.HeOpDagBuilder()
    self._ir_builder = compiler_subroutine_lowering.SubroutineLowering()

  def run(self):
    self._frontend_passes()
    self._backend_passes()

  def _frontend_passes(self):
    """Generates IR as the output for frontend."""

    # 1. Generate program AST.
    logging.info("-----------------")
    logging.info("AST construction:")
    parsed_ast = ast.parse(self._test_program)
    # 2. Transform the AST to add metadata for HE operations.
    transformed_ast = self._he_op_transformer.visit(parsed_ast)
    logging.info(ast.dump(transformed_ast))
    logging.info("-----------------")

    logging.info("-----------------")
    self._he_op_dag_builder.visit(transformed_ast)
    dag = self._he_op_dag_builder.graph
    self._he_op_dag_builder.add_num_limbs_attributes(self._initial_num_limbs)

    # 3. Build a DAG of HE operations and num_limbs.
    # Display the nodes and edges in the DAG with metadata
    logging.info("HE Operations DAG construction:")
    logging.info(type(dag))
    logging.info(f"Nodes in the DAG: {dag.nodes(data=True)}")
    logging.info("Edges in the DAG with metadata:")
    for edge in dag.edges(data=True):
      logging.info(edge)

    labels = {node: data.get('op', '') for node, data in dag.nodes(data=True)}
    plt.figure(figsize=(8, 6))
    nx.draw(dag,
            with_labels=True,
            labels=labels,
            node_color='skyblue',
            node_size=500,
            font_size=15,
            font_color='black',
            edge_color='gray')
    plt.savefig("he_ops_graph.png", format="PNG")
    logging.info("-----------------")

    # 4. Lower the DAG to IR.
    # dag = self._ir_builder.transform(dag)

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
