import js
from js import document, console, globalThis, update_textboxes, displayMessage, window
from pyodide.ffi import to_js, create_proxy
from pyodide.http import pyfetch

from Compiler import Compiler

import asyncio

# Global compiler instance
compiler = None


async def initialize_app():
    global compiler

    # Fetch the grammar file from the server
    response = await pyfetch("./python/grammar.txt")
    grammar_text = await response.string()

    # Now create the compiler
    compiler = WebInterface(grammar_text)
    js.compileProgram = create_proxy(compiler.compile_program_sync)

class WebInterface(Compiler):
    def __init__(self, grammar_text):
        super().__init__(grammar_text)
        """Load grammar and example program files"""
        document.getElementById('grammar').value = grammar_text
        document.getElementById('program').value = "// Enter your program here"

        # Enable compile button
        document.getElementById('compile-btn').disabled = False
        document.getElementById('options').disabled = False
        update_textboxes()


    def compile_program_sync(self):
        """Synchronous compile function called from JavaScript"""
        try:
            if compiler is None:
                document.getElementById('program-error').value = "Compiler not initialized yet. Please wait..."
                return

            # Get program text
            program_text = document.getElementById('program').value
            count = program_text.count('\n') + 1

            # Run compiler
            (tree, assembly, binary, error, execution_time,
             binary_to_assembly_mappings, code_mappings) = self._main(program_text)

            # Update UI with results
            parse_tree = document.getElementById('parse-tree')
            parse_tree.insertAdjacentHTML('beforeend', tree)
            document.getElementById('assembly').value = assembly
            document.getElementById('binary').value = binary
            document.getElementById('program-error').value = error

            compile_button = document.getElementById('run-program')

            if error == '':
                document.getElementById('program-error').value = "No errors - compilation successful!"
                displayMessage(f"Compilation completed in {execution_time}s", "success")
                compile_button.disabled = False
            else:
                displayMessage(f"Compilation resulted in errors: {error}", "error")
                compile_button.disabled = True

            update_textboxes()

        except Exception as e:
            import traceback
            displayMessage(f"Compilation error: {str(traceback.print_exc())}")
            document.getElementById('program-error').value = f"Compilation failed: {str(e)}"
            update_textboxes()
            document.getElementById('run-program').disabled = True

# Load files on startup
asyncio.ensure_future(initialize_app())