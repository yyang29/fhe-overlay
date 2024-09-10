import ast
import isa
import logging
import compiler_he_op_transformation


class Compiler():

  def __init__(self, test_program: str, assembly_output: str):
    self._test_program = test_program
    self._assembly_output = assembly_output
    self._he_op_transformer = compiler_he_op_transformation.HeOpTransformer()
    self._he_op_dag_builder = compiler_he_op_transformation.HeOpDagBuilder()

  def run(self):
    self._build_ast()

  def _build_ast(self):
    """Part of the frontend of the compiler."""

    parsed_ast = ast.parse(self._test_program)
    transformed_ast = self._he_op_transformer.visit(parsed_ast)

    logging.info(ast.dump(transformed_ast))

    self._he_op_dag_builder.visit(transformed_ast)
    dag = self._he_op_dag_builder.graph

    # Display the nodes and edges in the DAG with metadata
    logging.info(f"Nodes in the DAG: {dag.nodes(data=True)}")
    logging.info("Edges in the DAG with metadata:")
    for edge in dag.edges(data=True):
      logging.info(edge)
