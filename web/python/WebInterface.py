from pathlib import Path

from Compiler import Compiler


class WebInterface(Compiler):
    def __init__(self, grammar:str):
        super().__init__(grammar)


    def run(self, program: str):
        """
            Run the compiler pipeline and return a JSON-serializable dict.
        """
        tree, assembly, binary, error, execution_time = self._main(program)

        # Make sure everything is serializable (convert objects to strings if needed)
        return {
            "tree": str(tree),
            "assembly": str(assembly),
            "binary": binary,
            "error": str(error),
            "execution_time": float(execution_time) if execution_time is not None else None
        }


if __name__ == "__main__":
    grammar_file = Path('grammar.txt')
    test = WebInterface(grammar_file.read_text())
    grammar_file = Path('examples/raster_fill.txt')

    print((test.run(grammar_file.read_text())))

