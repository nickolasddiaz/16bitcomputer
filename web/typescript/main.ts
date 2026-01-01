import {emulator} from "./emulator.js";

declare const window: {
  runProgram: ((this: GlobalEventHandlers, ev: MouseEvent) => any) | null;
  openTab: (evt: Event, name: string) => void;
  update_textboxes: () => void;
  handleSidebar: (evt: Event, name: string) => void;
  choose_starter_program: () => Promise<void>;
  displayMessage: (message: string, type: string) => void;
} & Window;

let computer: emulator;

function setupLineNumbers(taId: string) {
    const ta: HTMLTextAreaElement = <HTMLTextAreaElement>document.getElementById(taId);
    const parent: HTMLElement = <HTMLElement>ta.parentElement;

    if (ta.parentElement == null || ta.parentElement.classList.contains("LN_wrapper")) {
        return;
    }
    const wrapper: HTMLDivElement = document.createElement("div");
    wrapper.id = taId + "_wrapper";
    wrapper.className = "LN_wrapper tab_content";
    parent.insertBefore(wrapper, ta);
    const sidebar:HTMLDivElement = document.createElement("div");
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

function updateLineNumbers(ta: HTMLTextAreaElement, sidebar:HTMLDivElement) {
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
    let registerId:HTMLElement = <HTMLElement>document.getElementById("register-id");
    let registerVal:HTMLElement = <HTMLElement>document.getElementById("register-val");
    let registers: HTMLTableCellElement[] = new Array(16);
    for (let i = 0; i < 16; i++) {
        const name: HTMLTableCellElement = document.createElement('td');
        name.textContent = `R${i}`;
        const value: HTMLTableCellElement = document.createElement('td');
        value.textContent = "0";
        registerId.appendChild(name);
        registerVal.appendChild(value);
        registers[i] = value;
    }

    computer = new emulator(
        <HTMLCanvasElement>document.getElementById("pixelCanvas"),
        <HTMLElement>document.getElementById("greater_id"),
        <HTMLElement>document.getElementById("equal_id"),
        <HTMLElement>document.getElementById("less_id"),
        registers, // table of 16
        <HTMLElement>document.getElementById("pc_id"),
        <HTMLElement>document.getElementById("instruct_id"),
    );

    const slider = document.getElementById("execute-time") as HTMLInputElement;
    const output = document.getElementById("execute-label") as HTMLElement;

    slider.oninput = () => {
        output.innerHTML = `Time per executions: ${String(2 ** Number(slider.value))} ms`;
        computer.timer = 2 ** Number(slider.value);
    };

    let runButton:HTMLButtonElement = document.getElementById("run-program") as HTMLButtonElement;
    runButton.onclick = window.runProgram;
    (<HTMLButtonElement>document.getElementById('compile-btn')).disabled = false;
    (<HTMLButtonElement>document.getElementById('options')).disabled = false;
    (<HTMLButtonElement>document.getElementById('run-program')).disabled = true;

});

window.runProgram = () => {
    computer.program = (<HTMLButtonElement>document.getElementById('binary')).value;
    computer.reset();
    computer.run();
};

window.openTab = (evt:Event, name:string) => {
    // Remove active class from all tablinks
    document.querySelectorAll(".tablinks").forEach(tablink => {
        tablink.classList.remove("active");
    });
    (evt.currentTarget as HTMLButtonElement).classList.add("active");

    // Hide all tab_content elements and LN_wrapper elements, except the computer panel
    document.querySelectorAll('.tab_content, .LN_wrapper').forEach(panel => {
        // Only hide those that are not 'computer'
        if (panel.id !== 'computer') {
            (panel as HTMLTextAreaElement).style.display = 'none';
        }
    });

    // Show the specific selected tab content or its wrapper
    const wrapper = document.getElementById(name + "_wrapper");
    const target = document.getElementById(name);

    if (wrapper) { // For textareas wrapped by LN_wrapper
        wrapper.style.display = "flex";
    } else if (target) { // For other div tab_content elements (like parse-tree)
        target.style.display = "block";
    }
};

window.handleSidebar = (evt: Event, name: string) => {
    const mainLayoutContainer:HTMLDivElement = <HTMLDivElement>document.querySelector('.main-content-layout'); // Target the main layout
    const computerPanel: HTMLButtonElement = <HTMLButtonElement>document.getElementById(name); // This is #computer

    if (computerPanel.style.display === "none") { // Sidebar is currently hidden, OPEN it
        computerPanel.style.display = "grid"; // Show it as a grid (its internal layout)
        mainLayoutContainer.classList.remove('sidebar-hidden'); // Restore two-column layout
        (<Element>evt.currentTarget).classList.add("active");
    } else { // Sidebar is currently visible,  CLOSE it
        computerPanel.style.display = "none"; // Hide it
        mainLayoutContainer.classList.add('sidebar-hidden'); // Make left content fill full width
        (<Element>evt.currentTarget).classList.remove("active");
    }
};


window.choose_starter_program = async () => {
    const selectedValue:string = (<HTMLSelectElement>document.getElementById("options")).value;
    if (selectedValue === "none") {
        (<HTMLButtonElement>document.getElementById('program')).value = "// Enter your program here";
        return;
    }
    await fetch("./examples/" + selectedValue + ".txt")
        .then(async response =>
            (<HTMLTextAreaElement>document.getElementById('program')).value = await response.text())
        .catch(error => window.displayMessage('Error fetching file:' + error, "error"));
    window.update_textboxes();
};

window.displayMessage = (message: string, type: string) => {
    const messageContainer:HTMLDivElement = <HTMLDivElement>document.getElementById('messageContainer');

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

(<HTMLDivElement>document.getElementById('closeMessage')).onclick = function() {
    const messageContainer:HTMLDivElement = <HTMLDivElement>document.getElementById('messageContainer');
    messageContainer.classList.remove('show', 'success', 'error');
    messageContainer.style.display = 'none';
};

// loading bar
window.addEventListener('load', function() {
    let progress = 0;
    const interval = setInterval(function() {
        progress += 10;
        (<HTMLDivElement>document.getElementById('loadingProgress')).style.width = progress + '%';
        if (progress >= 100) {
            clearInterval(interval);
            (<HTMLDivElement>document.getElementById('loadingOverlay')).style.display = 'none';
        }
    }, 100);

    ["program", "grammar", "assembly", "binary", "program-error"].forEach((id) => {
        setupLineNumbers(id);
    });
    (<HTMLButtonElement>document.querySelector('.tablinks.active')).click();
});

window.update_textboxes = () =>{
    ["program", "grammar", "assembly", "binary", "program-error"].forEach((id) => {
        (<HTMLTextAreaElement>document.getElementById(id)).dispatchEvent(new Event('input'));
    });
};
