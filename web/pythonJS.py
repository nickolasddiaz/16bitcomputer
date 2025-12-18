from WebInterface import WebInterface
from js import document, console, displayMessage
import asyncio

# Global compiler instance
compiler = None


async def load_files():
    """Load grammar and example program files"""
    try:
        # Read grammar file directly from the virtual filesystem
        with open('./grammar.txt', 'r') as f:
            grammar_text = f.read()
        document.getElementById('grammar').value = grammar_text

        # Initialize compiler
        global compiler
        compiler = WebInterface(grammar_text)

        document.getElementById('program').value = "// Enter your program here"

        # Enable compile button
        document.getElementById('compile-btn').disabled = False
        document.getElementById('options').disabled = False

    except Exception as e:
        console.error(f"Error loading files: {e}")
        # Make sure to provide feedback in the UI
        error_message = f"Error during initialization: {e}"
        document.getElementById('grammar').value = error_message
        document.getElementById('program').value = error_message
        document.getElementById('program-error').value = error_message


def compile_program_sync():
    """Synchronous compile function called from JavaScript"""
    try:
        if compiler is None:
            document.getElementById('program-error').value = "Compiler not initialized yet. Please wait..."
            return

        # Get program text
        program_text = document.getElementById('program').value

        # Run compiler
        result = compiler.run(program_text)

        # Update UI with results
        parse_tree = document.getElementById('parse-tree')
        parse_tree.insertAdjacentHTML('beforeend', result['tree'])
        document.getElementById('assembly').value = result['assembly']
        document.getElementById('binary').value = str(result['binary'])
        document.getElementById('program-error').value = result['error']

        if result['error'] == '':
            document.getElementById('program-error').value = "No errors - compilation successful!"
            displayMessage(f"Compilation completed in {result['execution_time']}s", "success")
        else:
            displayMessage(f"Compilation resulted in errors: {result['error']}", "error")

    except Exception as e:
        displayMessage(f"Compilation error: {e}")
        document.getElementById('program-error').value = f"Compilation failed: {str(e)}"


# Export function to JavaScript
import js

js.compileProgram = compile_program_sync

# Load files on startup
asyncio.ensure_future(load_files())