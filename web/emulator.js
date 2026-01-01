var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
const CANVAS_SIZE = 32;
const COLOR_SIZE = 32;
const REG_SIZE = 16;
const STACK_POINTER = 15;
const DATA = {
    None: 0, IMM8: 1, REG: 2, RAM: 3,
    REG_REG: 4, REG_IMM8: 5, REG_RAM: 6, RAM_REG: 7, RAM_IMM8: 8, RAM_RAM: 9
};
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
export class emulator {
    set program(hex_string) {
        hex_string = hex_string.replace(/\s/g, '');
        const uint16Array = new Uint16Array(hex_string.length / 4);
        for (let i = 0; i < hex_string.length; i += 4) {
            const hexChunk = hex_string.substring(i, i + 4);
            uint16Array[i / 4] = parseInt(hexChunk, 16);
        }
        this._program = uint16Array;
    }
    set timer(value) {
        this._timer = value;
    }
    stop() {
        this.compile_btn.disabled = true;
        this.options_btn.disabled = true;
        this.run_btn.disabled = false;
        this.go = false;
    }
    toggle_go() {
        this.compile_btn.disabled = true;
        this.options_btn.disabled = true;
        this.run_btn.disabled = false;
        this.go = true;
    }
    reset() {
        this.canvas.reset();
        this.status_flags.reset();
        this.ram.fill(0);
        this.register.reset();
        this.pc.reset();
        this.toggle_go();
    }
    constructor(canvas, greater_element, equal_element, less_element, register_id, program_counter_element, instruct_element) {
        this.ram = new Uint16Array(0xFFFF);
        this.canvas = new Canvas(canvas);
        this.status_flags = new StatusFlags(greater_element, equal_element, less_element);
        this.register = new Register(register_id);
        this.pc = new ProgramCounter(program_counter_element);
        this.go = false;
        this.op = new Map();
        this._timer = 1;
        this.program = "";
        this.start_canvas_timer = performance.now();
        this.instruct_element = instruct_element;
        this.compile_btn = document.getElementById('compile-btn');
        this.options_btn = document.getElementById('options');
        this.run_btn = document.getElementById('run-program');
        let arith_data = [DATA.REG_REG, DATA.RAM_REG, DATA.REG_IMM8, DATA.REG_RAM, DATA.RAM_IMM8, DATA.RAM_RAM];
        let arith = [this.MOV.bind(this), this.status_flags.CMP.bind(this.status_flags), this.ADD.bind(this), this.SUB.bind(this), this.MULT.bind(this), this.DIV.bind(this), this.QUOT.bind(this), this.AND.bind(this), this.OR.bind(this), this.XOR.bind(this), this.SHL.bind(this), this.SHR.bind(this), this.NEG.bind(this), this.NOT.bind(this)];
        let one_data = [DATA.IMM8, DATA.REG, DATA.RAM];
        let one = [this.PUSH.bind(this), this.POP.bind(this), this.canvas.VID_RED.bind(this.canvas), this.canvas.VID_GREEN.bind(this.canvas), this.canvas.VID_BLUE.bind(this.canvas), this.canvas.VID_X.bind(this.canvas), this.canvas.VID_Y.bind(this.canvas)];
        let jump = [this.pc.JMP.bind(this.pc), this.JEQ.bind(this), this.JNE.bind(this), this.JG.bind(this), this.JLE.bind(this), this.JL.bind(this), this.JGE.bind(this), this.CALL.bind(this)];
        let i = 0;
        this.op.set(i++, [this.NOP.bind(this), DATA.None]);
        this.op.set(i++, [this.HALT.bind(this), DATA.None]);
        this.op.set(i++, [this.canvas.VID.bind(this.canvas), DATA.None]);
        for (const op of one) {
            for (const data of one_data) {
                this.op.set(i++, [op, data]);
            }
        }
        for (const op of arith) {
            for (const data of arith_data) {
                this.op.set(i++, [op, data]);
            }
        }
        for (const op of jump) {
            this.op.set(i++, [op, DATA.IMM8]);
        }
        this.op.set(i++, [this.RTRN.bind(this), DATA.None]);
    }
    run() {
        return __awaiter(this, void 0, void 0, function* () {
            let program_start = performance.now();
            while (this.go) {
                while (performance.now() - (program_start + this._timer) < 4) { //measured in milliseconds
                    yield sleep(1);
                }
                program_start = performance.now();
                yield sleep(this._timer);
                if (performance.now() - this.start_canvas_timer > 100) {
                    this.start_canvas_timer = performance.now();
                    this.canvas.render();
                }
                let temp = this._program[this.pc.count];
                let instruct = (temp >> 8);
                let reg2 = temp & 0x000F;
                let reg1 = (temp & 0x00F0) >> 4;
                let temp1 = this.op.get(instruct);
                let data_type = temp1[1];
                let operand = temp1[0];
                let name = operand.name;
                if (name.startsWith('bound ')) {
                    name = name.substring(6);
                }
                let instruct_name = name;
                let item1;
                let item2;
                let index;
                switch (data_type) {
                    case DATA.REG_REG:
                        item1 = this.register.getRegItem(reg1);
                        item2 = this.register.getRegItem(reg2);
                        operand(item2, item1, this.register.setRegItem.bind(this.register, reg1));
                        instruct_name += ` ${item2} ${item1}`;
                        break;
                    case DATA.REG_IMM8:
                        item1 = this.register.getRegItem(reg1);
                        this.pc.next();
                        item2 = this._program[this.pc.count];
                        operand(item2, item1, this.register.setRegItem.bind(this.register, reg1));
                        instruct_name += ` ${item2} ${item1}`;
                        break;
                    case DATA.REG_RAM:
                        item1 = this.register.getRegItem(reg1);
                        this.pc.next();
                        item2 = this.ram[this._program[this.pc.count]];
                        operand(item2, item1, this.register.setRegItem.bind(this.register, reg1));
                        instruct_name += ` ${item2} ${item1}`;
                        break;
                    case DATA.RAM_REG:
                        this.pc.next();
                        index = this._program[this.pc.count];
                        item1 = this.ram[index];
                        item2 = this.register.getRegItem(reg1);
                        operand(item2, item1, this.save_ram.bind(this, index));
                        instruct_name += ` ${item2} ${item1}`;
                        break;
                    case DATA.RAM_IMM8:
                        this.pc.next();
                        index = this._program[this.pc.count];
                        item1 = this.ram[index];
                        this.pc.next();
                        item2 = this._program[this.pc.count];
                        operand(item2, item1, this.save_ram.bind(this, index));
                        instruct_name += ` ${item2} ${item1}`;
                        break;
                    case DATA.RAM_RAM:
                        this.pc.next();
                        index = this._program[this.pc.count];
                        item1 = this.ram[index];
                        this.pc.next();
                        let index2 = this._program[this.pc.count];
                        item2 = this.ram[index2];
                        operand(item2, item1, this.save_ram.bind(this, index));
                        instruct_name += ` ${item2} ${item1}`;
                        break;
                    case DATA.REG:
                        item1 = this.register.getRegItem(reg1);
                        operand(item1);
                        instruct_name += ` ${item1}`;
                        break;
                    case DATA.IMM8:
                        this.pc.next();
                        item1 = this._program[this.pc.count];
                        operand(item1);
                        instruct_name += ` ${item1}`;
                        break;
                    case DATA.RAM:
                        this.pc.next();
                        item1 = this.ram[this._program[this.pc.count]];
                        operand(item1);
                        instruct_name += ` ${item1}`;
                        break;
                    case DATA.None:
                        operand();
                        break;
                }
                this.instruct_element.textContent = instruct_name;
                this.pc.next();
            }
            this.canvas.render();
        });
    }
    save_ram(index, value) {
        this.ram[index] = value;
    }
    MOV(value1, _value2, set) { set(value1); }
    ADD(value1, value2, set) { set(value1 + value2); }
    SUB(value1, value2, set) { set(value1 - value2); }
    MULT(value1, value2, set) { set(value1 * value2); }
    DIV(value1, value2, set) {
        if (value2 === 0)
            set(0);
        else
            set(Math.floor(value1 / value2));
    }
    QUOT(value1, value2, set) {
        if (value2 === 0)
            set(0);
        else
            set(value1 % value2);
    }
    AND(value1, value2, set) { set(value1 & value2); }
    OR(value1, value2, set) { set(value1 | value2); }
    XOR(value1, value2, set) { set(value1 ^ value2); }
    SHL(value1, value2, set) { set(value1 << value2); }
    SHR(value1, value2, set) { set(value1 >> value2); }
    NEG(value1, value2, set) { set(-value1); }
    NOT(value1, value2, set) { set(~value1); }
    JEQ(value) { if (this.status_flags.equal)
        this.pc.JMP(value); }
    JNE(value) { if (!this.status_flags.equal)
        this.pc.JMP(value); }
    JG(value) { if (this.status_flags.greater)
        this.pc.JMP(value); }
    JLE(value) { if (this.status_flags.less || this.status_flags.equal)
        this.pc.JMP(value); }
    JL(value) { if (this.status_flags.less)
        this.pc.JMP(value); }
    JGE(value) { if (this.status_flags.greater || this.status_flags.equal)
        this.pc.JMP(value); }
    CALL(value) {
        let sp = this.register.getRegItem(STACK_POINTER);
        this.ram[sp + 1] = this.pc.count;
        this.pc.JMP(value);
    }
    RTRN() {
        let sp = this.register.getRegItem(STACK_POINTER);
        this.pc.JMP(this.ram[sp + 1]);
    }
    NOP() { }
    HALT() { this.go = true; }
    PUSH(value) {
        this.save_ram(this.register.getRegItem(STACK_POINTER), value);
        this.register.add_stack_pt();
    }
    POP(value) {
        this.register.sub_stack_pt();
        this.save_ram(this.register.getRegItem(STACK_POINTER), value);
    }
}
class Canvas {
    constructor(canvas) {
        // XTerm256 color model (8-bit)
        // using rgb555Data, a 16-bit integer containing RRRRR GGGGG BBBBB
        this.ctx = canvas.getContext('2d');
        this.imageData = this.ctx.createImageData(CANVAS_SIZE, CANVAS_SIZE);
        this.data = this.imageData.data;
        this.reset();
    }
    reset() {
        this.fill_back();
        this.x = 0;
        this.y = 0;
        this.r = 0;
        this.g = 0;
        this.b = 0;
    }
    VID_X(val) { this.x = val % CANVAS_SIZE; }
    VID_Y(val) { this.y = val % CANVAS_SIZE; }
    VID_RED(val) { this.r = (val % COLOR_SIZE) * 8; }
    VID_GREEN(val) { this.g = (val % COLOR_SIZE) * 8; }
    VID_BLUE(val) { this.b = (val % COLOR_SIZE) * 8; }
    fill_back() {
        for (let y = 0; y < CANVAS_SIZE; y++) {
            for (let x = 0; x < CANVAS_SIZE; x++) {
                const index = (y * CANVAS_SIZE + x) * 4;
                // Set the color values (0-255)
                this.data[index] = 0; // Red
                this.data[index + 1] = 0; // Green
                this.data[index + 2] = 0; // Blue
                this.data[index + 3] = 255; // Alpha (opacity, 0-255)
            }
        }
        this.ctx.putImageData(this.imageData, 0, 0);
    }
    VID() {
        const index = (this.y * CANVAS_SIZE + this.x) * 4;
        // Set the color values (0-255)
        this.data[index] = this.r; // Red
        this.data[index + 1] = this.g; // Green
        this.data[index + 2] = this.b; // Blue
        this.data[index + 3] = 255; // Alpha (opacity, 0-255)
    }
    render() {
        this.ctx.putImageData(this.imageData, 0, 0);
    }
}
class StatusFlags {
    constructor(greater_element, equal_element, less_element) {
        this._greater = false;
        this._equal = false;
        this._less = false;
        this.greater_cell = greater_element;
        this.equal_cell = equal_element;
        this.less_cell = less_element;
        this.reset();
    }
    reset() {
        this.greater_cell.textContent = '0';
        this.equal_cell.textContent = '0';
        this.less_cell.textContent = '0';
        this._greater = false;
        this._equal = false;
        this._less = false;
    }
    get greater() { return this._greater; }
    get equal() { return this._equal; }
    get less() { return this._less; }
    CMP(value1, value2) {
        let equal = value2 === value1;
        this.equal_cell.textContent = equal ? '1' : '0';
        this._equal = equal;
        let greater = value2 > value1;
        this.greater_cell.textContent = greater ? '1' : '0';
        this._greater = greater;
        let less = value2 < value1;
        this.less_cell.textContent = less ? '1' : '0';
        this._less = less;
    }
}
class Register {
    constructor(cell_id) {
        this.reg = new Int16Array(REG_SIZE);
        this.cells = cell_id;
        this.reset();
    }
    reset() {
        this.reg.fill(0);
        for (let i = 0; i < REG_SIZE; i++) {
            if (this.cells[i]) {
                this.cells[i].textContent = String(0);
            }
        }
    }
    setRegItem(index, value) {
        this.reg[index] = value;
        this.cells[index].textContent = String(value);
    }
    getRegItem(index) {
        return this.reg[index];
    }
    sub_stack_pt() {
        // @ts-ignore
        this.setRegItem(STACK_POINTER, this.reg[STACK_POINTER] - 1);
    }
    add_stack_pt() {
        // @ts-ignore
        this.setRegItem(STACK_POINTER, this.reg[STACK_POINTER] + 1);
    }
}
class ProgramCounter {
    constructor(pc_element) {
        this.pc_cell = pc_element;
        this.pc_cell.textContent = String(0);
        this.reset();
    }
    reset() {
        this.pc_cell.textContent = String(0);
        this.count = 0;
    }
    JMP(value) {
        this.pc_cell.textContent = String(value - 1);
        this.count = value - 1;
    }
    next() {
        this.count += 1;
        this.pc_cell.textContent = String(this.count);
    }
}
