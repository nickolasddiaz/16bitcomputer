import {emulator} from './emulator.js';
let computer;

function setupLineNumbers(taId) {
    const ta = document.getElementById(taId);
    const parent = ta.parentElement;

    if (!ta.parentElement.classList.contains("LN_wrapper")) {
        const wrapper = document.createElement("div");
        wrapper.id = taId + "_wrapper";
        wrapper.className = "LN_wrapper tab_content";
        parent.insertBefore(wrapper, ta);

        const sidebar = document.createElement("div");
        sidebar.className = "LN_sb";

        wrapper.appendChild(sidebar);
        wrapper.appendChild(ta);

        ta.classList.add("LN_ta");
        ta.classList.remove("tab_content");

        ta.addEventListener("scroll", () => {
            sidebar.scrollTop = ta.scrollTop;
        });

        ta.addEventListener("input", () => updateLineNumbers(ta, sidebar));

        updateLineNumbers(ta, sidebar);
    }
}

function updateLineNumbers(ta, sidebar) {
    const lines = ta.value.split('\n').length;
    let lineNumbersHtml = '';
    for (let i = 1; i <= lines; i++) {
        lineNumbersHtml += i + '<br>';
    }
    // Only update DOM if content changed to prevent flicker
    if (sidebar.innerHTML !== lineNumbersHtml) {
        sidebar.innerHTML = lineNumbersHtml;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Initialize registers table
    let registerId = document.getElementById("register-id");
    let registerVal = document.getElementById("register-val");
    let registers = new Array(16);
    for (let i = 0; i < 16; i++) {
        const name = document.createElement('td');
        name.textContent = `R${i}`;
        const value = document.createElement('td');
        value.textContent = "0";
        registerId.appendChild(name);
        registerVal.appendChild(value);
        registers[i] = value;
    }

    computer = new emulator(
        document.getElementById("pixelCanvas"),
        document.getElementById("greater_id"),
        document.getElementById("equal_id"),
        document.getElementById("less_id"),
        registers, // table of 16
        document.getElementById("pc_id"),
        document.getElementById("instruct_id"),
    );

    const slider = document.getElementById("execute-time");
    const output = document.getElementById("execute-label");

    slider.oninput = function() {
        output.innerHTML = `Time per executions: ${String(2 ** this.value)} ms`;
        computer.timer = 2 ** this.value
    }

    let runButton = document.getElementById("run-program");
    runButton.onclick = runProgram;
    document.getElementById('compile-btn').disabled = false;
    document.getElementById('options').disabled = false;
    document.getElementById('run-program').disabled = false;
});

window.runProgram = () => {
    computer.program = document.getElementById('binary').value;
    computer.reset();
    computer.run();
};

window.openTab = (evt, name) => {
    let i, tabcontent, tablinks;

    // Hide all tab content
    tabcontent = document.getElementsByClassName("tab_content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }

    // Also hide all LN_wrapper elements
    const wrappers = document.getElementsByClassName("LN_wrapper");
    for (i = 0; i < wrappers.length; i++) {
        wrappers[i].style.display = "none";
    }

    // Remove active class from all tabs
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    // Show the selected tab
    const wrapper = document.getElementById(name + "_wrapper");
    const target = document.getElementById(name);

    if (wrapper) {
        wrapper.style.display = "flex";
    } else if (target) {
        target.style.display = "block";
    }

    evt.currentTarget.className += " active";
};

window.choose_starter_program = async () => {
    const selectedValue = document.getElementById("options").value;
    if (selectedValue === "none") {
        document.getElementById('program').value = "// Enter your program here";
        return;
    }
    await fetch("./examples/" + selectedValue + ".txt")
        .then(async response =>
            document.getElementById('program').value = await response.text())
        .catch(error => displayMessage('Error fetching file:' + error, "error"));
    update_textboxes();
};

window.displayMessage = (message, type) => {
    const messageContainer = document.getElementById('messageContainer');

    let textSpan = messageContainer.querySelector('.message-text');
    if (!textSpan) {
        textSpan = document.createElement('span');
        textSpan.className = 'message-text';
        messageContainer.appendChild(textSpan);
    }

    textSpan.textContent = message;
    messageContainer.className = `message-container show ${type}`;
    messageContainer.style.display = 'block';
};

document.getElementById('closeMessage').onclick = function() {
    const messageContainer = document.getElementById('messageContainer');
    messageContainer.classList.remove('show', 'success', 'error');
    messageContainer.style.display = 'none';
};

// loading bar
window.addEventListener('load', function() {
    let progress = 0;
    const interval = setInterval(function() {
        progress += 10;
        document.getElementById('loadingProgress').style.width = progress + '%';
        if (progress >= 100) {
            clearInterval(interval);
            document.getElementById('loadingOverlay').style.display = 'none';
        }
    }, 100);

    // Append Line Numbers
    ["program", "grammar", "assembly", "binary", "program-error"].forEach((id) => {
        setupLineNumbers(id);
    });
    openTab(document.getElementById('program'), 'program');
});

window.update_textboxes = () =>{
    ["program", "grammar", "assembly", "binary", "program-error"].forEach((id) => {
        document.getElementById(id).dispatchEvent(new Event('input'));
    });
}
