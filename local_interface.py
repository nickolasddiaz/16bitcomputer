from pathlib import Path
from compiler import Compiler


class LocalInterface(Compiler):
    def __init__(self):
        super().__init__(self.get_grammar())

    def run(self):
        program: str = self.get_program()
        tree, assembly, binary, error, execution_time  = self._main(program)

        if tree:
            self.write_parse_tree(tree)

        if assembly:
            self.write_assembly(assembly)

        if binary:
            self.write_binary(binary)

        if error:
            self.write_error(error)

        if execution_time != 0:
            self.print_success(execution_time)

    def get_grammar(self) -> str:
        grammar_file = Path('grammar.txt')
        return grammar_file.read_text()

    def get_program(self) -> str:
        grammar_file = Path('examples/example.txt')
        return grammar_file.read_text()

    def write_parse_tree(self, parse_tree:str) -> None:
        Path('program.tre').write_text(parse_tree)

    def write_assembly(self, asm_str: str) -> None:
        Path('program.asm').write_text(asm_str)

    def write_binary(self, binary_str: str) -> None:
        Path('program.bin').write_text(binary_str)

    def write_error(self, error_str: str) -> None:
        print(f"\033[31m{error_str}\033[0m")
        Path('program.error').write_text(error_str)

    def print_success(self, execution_time: float) -> None:
        print(f"Program successfully compiled! Execution time: {execution_time:.6f} seconds!")


if __name__ == "__main__":
    test = LocalInterface()
    test.run()