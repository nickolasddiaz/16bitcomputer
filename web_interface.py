from compiler import Compiler


class WebInterface(Compiler):
    def __init__(self, grammar:str):
        super().__init__(grammar)


    def run(self, program: str):
        tree, assembly, binary, error, execution_time  = self._main(program)

