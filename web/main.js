var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
import { emulator } from "./emulator.js";
let computer;
function setupLineNumbers(taId) {
    const ta = document.getElementById(taId);
    const parent = ta.parentElement;
    if (ta.parentElement == null || ta.parentElement.classList.contains("LN_wrapper")) {
        return;
    }
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
    computer = new emulator(document.getElementById("pixelCanvas"), document.getElementById("greater_id"), document.getElementById("equal_id"), document.getElementById("less_id"), registers, // table of 16
    document.getElementById("pc_id"), document.getElementById("instruct_id"));
    const slider = document.getElementById("execute-time");
    const output = document.getElementById("execute-label");
    slider.oninput = () => {
        output.innerHTML = `Time per executions: ${String(Math.pow(2, Number(slider.value)))} ms`;
        computer.timer = Math.pow(2, Number(slider.value));
    };
    let runButton = document.getElementById("run-program");
    runButton.onclick = window.runProgram;
    document.getElementById('compile-btn').disabled = false;
    document.getElementById('options').disabled = false;
    document.getElementById('run-program').disabled = true;
});
window.runProgram = () => {
    computer.program = document.getElementById('binary').value;
    computer.reset();
    computer.run();
};
window.openTab = (evt, name) => {
    // Remove active class from all tablinks
    document.querySelectorAll(".tablinks").forEach(tablink => {
        tablink.classList.remove("active");
    });
    evt.currentTarget.classList.add("active");
    // Hide all tab_content elements and LN_wrapper elements, except the computer panel
    document.querySelectorAll('.tab_content, .LN_wrapper').forEach(panel => {
        // Only hide those that are not 'computer'
        if (panel.id !== 'computer') {
            panel.style.display = 'none';
        }
    });
    // Show the specific selected tab content or its wrapper
    const wrapper = document.getElementById(name + "_wrapper");
    const target = document.getElementById(name);
    if (wrapper) { // For textareas wrapped by LN_wrapper
        wrapper.style.display = "flex";
    }
    else if (target) { // For other div tab_content elements (like parse-tree)
        target.style.display = "block";
    }
};
window.handleSidebar = (evt, name) => {
    const mainLayoutContainer = document.querySelector('.main-content-layout'); // Target the main layout
    const computerPanel = document.getElementById(name); // This is #computer
    if (computerPanel.style.display === "none") { // Sidebar is currently hidden, OPEN it
        computerPanel.style.display = "grid"; // Show it as a grid (its internal layout)
        mainLayoutContainer.classList.remove('sidebar-hidden'); // Restore two-column layout
        evt.currentTarget.classList.add("active");
    }
    else { // Sidebar is currently visible,  CLOSE it
        computerPanel.style.display = "none"; // Hide it
        mainLayoutContainer.classList.add('sidebar-hidden'); // Make left content fill full width
        evt.currentTarget.classList.remove("active");
    }
};
window.choose_starter_program = () => __awaiter(void 0, void 0, void 0, function* () {
    const selectedValue = document.getElementById("options").value;
    if (selectedValue === "none") {
        document.getElementById('program').value = "// Enter your program here";
        return;
    }
    yield fetch("./examples/" + selectedValue + ".txt")
        .then((response) => __awaiter(void 0, void 0, void 0, function* () { return document.getElementById('program').value = yield response.text(); }))
        .catch(error => window.displayMessage('Error fetching file:' + error, "error"));
    window.update_textboxes();
});
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
document.getElementById('closeMessage').onclick = function () {
    const messageContainer = document.getElementById('messageContainer');
    messageContainer.classList.remove('show', 'success', 'error');
    messageContainer.style.display = 'none';
};
// loading bar
window.addEventListener('load', function () {
    let progress = 0;
    const interval = setInterval(function () {
        progress += 10;
        document.getElementById('loadingProgress').style.width = progress + '%';
        if (progress >= 100) {
            clearInterval(interval);
            document.getElementById('loadingOverlay').style.display = 'none';
        }
    }, 100);
    ["program", "grammar", "assembly", "binary", "program-error"].forEach((id) => {
        setupLineNumbers(id);
    });
    document.querySelector('.tablinks.active').click();
});
window.update_textboxes = () => {
    ["program", "grammar", "assembly", "binary", "program-error"].forEach((id) => {
        document.getElementById(id).dispatchEvent(new Event('input'));
    });
};
