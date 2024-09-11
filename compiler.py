import ast
import isa
import logging
import compiler_he_op_transformation


class Compiler():

  def __init__(self, test_program: str, assembly_output: str,
               initial_num_limbs: int):
    self._test_program = test_program
    self._assembly_output = assembly_output
    self._initial_num_limbs = initial_num_limbs
    self._he_op_transformer = compiler_he_op_transformation.HeOpTransformer()
    self._he_op_dag_builder = compiler_he_op_transformation.HeOpDagBuilder()

  def run(self):
    self._frontend_passes()

  def _frontend_passes(self):
    """Generates IR as the output for frontend."""

    parsed_ast = ast.parse(self._test_program)
    transformed_ast = self._he_op_transformer.visit(parsed_ast)

    logging.info(ast.dump(transformed_ast))

    self._he_op_dag_builder.visit(transformed_ast)
    dag = self._he_op_dag_builder.graph

    self._he_op_dag_builder.add_num_limbs_attributes(self._initial_num_limbs)

    # Display the nodes and edges in the DAG with metadata
    logging.info("-----------------")
    logging.info(type(dag))
    logging.info(f"Nodes in the DAG: {dag.nodes(data=True)}")
    logging.info("Edges in the DAG with metadata:")
    for edge in dag.edges(data=True):
      logging.info(edge)
