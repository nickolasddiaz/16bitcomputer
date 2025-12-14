const CANVAS_SIZE = 64;
const COLOR_SIZE = 32;
const REG_SIZE = 0xF;

const DATA = Object.freeze({
    REG_REG: 0,
    REG_IMM8: 1,
    REG_RAM: 2,
    RAM_REG: 3,
    RAM_RAM: 4,
    RAM_IMM8: 6,
    IMM8: 7,
    REG: 8,
    RAM: 9,
    None: 10,
})


class emulator{
    #ram; #canvas; #status_flags; #register; #program_counter; #program
    constructor(canvas, status_flags, register, program_counter, program) {
        this.ram = new Int16Array(0xFFFF);
        this.stack_pointer = 0;
        this.canvas = canvas;
        this.status_flags = status_flags;
        this.register = register;
        this.program_counter = program_counter;
        this.program = program;
        this.stop = false;

        // shoving commands into a hashmap very messy

        let arith_data = [DATA.REG_REG, DATA.RAM_REG, DATA.REG_IMM8, DATA.REG_RAM, DATA.RAM_IMM8, DATA.RAM_RAM];
        let arith = [this.MOV, this.status_flags.CMP, this.ADD, this.SUB, this.MULT, this.DIV, this.QUOT, this.AND, this.OR, this.XOR, this.SHL, this.SHR];

        let one_data = [DATA.IMM8, DATA.REG, DATA.RAM];
        let one = [this.canvas.VID, this.canvas.VID_RED, this.canvas.VID_GREEN, this.canvas.VID_BLUE, this.canvas.VID_X, this.canvas.VID_Y];
        let one_2 = [this.NEG, this.NOT];

        let jump = [this.program_counter.JMP, this.JEQ, this.JNE, this.JG, this.JLE, this.JL, this.JGE, this.CALL]


        this.op = new Map();
        let i = 0;

        this.op.set(i++, [this.NOP, DATA.None]);
        this.op.set(i++, [this.HALT, DATA.None]);

        for (const op in one_data){
            for (const data in one) {
                this.op.set(i++, [op, data]);
            }
        }

        for (const op in arith){
            for (const data in arith_data) {
                this.op.set(i++, [op, data]);
            }
        }

        for (const op in one_data){
            for (const data in one_2) {
                this.op.set(i++, [op, data]);
            }
        }
        for (const op in jump){
            this.op.set(i++, [op, DATA.IMM8]);

        }
        this.op.set(i++, [this.RTRN, DATA.None]);

    }
    MOV(value1, value2, set){set(value1);}
    ADD(value1, value2, set){set(value1 + value2);}
    SUB(value1, value2, set){set(value1 - value2);}
    MULT(value1, value2, set){set(value1 * value2);}
    DIV(value1, value2, set){
        if (value2 === 0)
            set(0);
        set(value1 - value2);
    }
    QUOT(value1, value2, set){
        if (value2 === 0)
            set(0);
        set(value1 % value2);
    }
    AND(value1, value2, set){set(value1 & value2);}
    OR(value1, value2, set){set(value1 | value2);}
    XOR(value1, value2, set){set(value1 ^ value2);}
    SHL(value1, value2, set){set(value1 << value2);}
    SHR(value1, value2, set){set(value1 >> value2);}

    JEQ(value){if (this.status_flags.equal) this.program_counter.JMP(value);}
    JNE(value){if (!this.status_flags.equal) this.program_counter.JMP(value);}
    JG(value){if (this.status_flags.greater) this.program_counter.JMP(value);}
    JLE(value){if (this.status_flags.less || this.status_flags.equal) this.program_counter.JMP(value);}
    JL(value){if (this.status_flags.less) this.program_counter.JMP(value);}
    JGE(value){if (this.status_flags.greater || this.status_flags.equal) this.program_counter.JMP(value);}
    CALL(value){
        this.ram[this.stack_pointer] = this.program_counter.JMP;
        this.program_counter.JMP(value);
    }
    RTRN(){
        this.program_counter.JMP(this.ram[this.stack_pointer]);
    }

    NEG(value, set){set(-value);}
    NOT(value, set){set(~value);}
    NOP(){}
    HALT(){this.stop = true}
}

class Canvas {
    #ctx
    #imageData
    #data
    #x; #y; #r; #g; #b

    constructor(canvas) {
        // XTerm256 color model (8-bit)
        // using rgb555Data, a 16-bit integer containing RRRRR GGGGG BBBBB
        this.#ctx = canvas.getContext('2d');
        this.#imageData = this.#ctx.createImageData(CANVAS_SIZE, CANVAS_SIZE);
        this.#data = this.#imageData.#data;
    }
    reset(){
        this.fill_back();
        this.#x = 0;
        this.#y = 0;
        this.#r = 0;
        this.#g = 0;
        this.#b = 0;
    }
    set VID_X(val){ this.#x = val & CANVAS_SIZE;}
    set VID_Y(val){ this.#y = val & CANVAS_SIZE;}

    set VID_RED(val){ this.#r = val & COLOR_SIZE * 4;}
    set VID_GREEN(val){ this.#g = val & COLOR_SIZE * 4;}
    set VID_BLUE(val){ this.#b = val & COLOR_SIZE * 4;}

    fill_back(){
        for (let y = 0; y < CANVAS_SIZE; y++) {
            for (let x = 0; x < CANVAS_SIZE; x++) {
                    const index = (y * CANVAS_SIZE + x) * 4;

                    // Set the color values (0-255)
                    this.#data[index] = 0;         // Red
                    this.#data[index + 1] = 0;     // Green
                    this.#data[index + 2] = 0;     // Blue
                    this.#data[index + 3] = 255;   // Alpha (opacity, 0-255)
            }
        }
        this.#ctx.putImageData(this.#imageData, 0, 0);
    }

    VID() {
        const index = (this.#y * CANVAS_SIZE + this.#x) * 4;

        // Set the color values (0-255)
        this.#data[index] = this.#r;         // Red
        this.#data[index + 1] = this.#g;     // Green
        this.#data[index + 2] = this.#b;     // Blue
        this.#data[index + 3] = 255;   // Alpha (opacity, 0-255)

        this.#ctx.putImageData(this.#imageData, 0, 0);
    }
}

class StatusFlags{
    #greater; #less; #equal
    #greater_cell
    #equal_cell
    #less_cell
    constructor(greater_id, equal_id, less_id) {
        this.greater = false;
        this.equal = false;
        this.less = false;
        this.greater_cell = document.getElementById(greater_id);
        this.equal_cell = document.getElementById(equal_id);
        this.less_cell = document.getElementById(less_id);
        this.reset();
    }
    reset(){
        this.#greater_cell.value = '0';
        this.#equal_cell.value = '0';
        this.#less_cell.value = '0';
    }

    get greater(){ return this.#greater_cell;}
    get equal(){ return this.#equal_cell;}
    get less(){ return this.#less_cell;}

    CMP(value1, value2){
        let equal = value1 === value2;
        this.equal_cell.value = equal ? '1':'0';
        this.equal= equal;

        let greater = value1 <= value2;
        this.greater_cell.value = greater ? '1':'0';
        this.greater= greater;

        this.less_cell.value = greater ? '0':'1';
        this.less= !greater;
    }
}

class Register {
    #reg;
    #cells;
    constructor(cell_id) {
        this.#reg = new Int16Array(REG_SIZE);
        this.#cells = new Array(REG_SIZE);

        for (let i = 0; i < REG_SIZE; i++){
            this.#cells[i] = document.getElementById(`${cell_id}-${i}`);
        }

        this.reset();
    }

    reset(){
        this.#reg.fill(0);
        for (let i = 0; i < REG_SIZE; i++){
            if (this.#cells[i]) {
                this.#cells[i].value = 0;
            }
        }
    }
    setRegItem(index, value){
        this.#reg[index] = value;
        this.#cells[index].value = value;
    }

    getRegItem(index){
        return this.#reg[index];
    }

}

class program_counter{
    #pc; #pc_cell
    constructor(pc_id) {
        this.#pc_cell = document.getElementById(pc_id);
        this.reset();
    }
    reset(){
        this.#pc_cell.value = 0;
        this.#pc = 0;
    }
    get pc(){ return this.#pc}
    JMP(value){
        this.#pc_cell.value = value;
        this.#pc_cell = value;
    }
    next(){
        this.#pc_cell.value += 16;
        this.#pc_cell += 16;
    }
}


