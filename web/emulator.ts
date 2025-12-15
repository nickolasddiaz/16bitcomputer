const CANVAS_SIZE: number = 64;
const COLOR_SIZE: number = 32;
const REG_SIZE: number = 0xF;
const INSTRUCTION_BUS: number = 0xF;
const STACK_POINTER: number = 15;


enum DATA {
    None, IMM8, REG, RAM,
    REG_REG, REG_IMM8, REG_RAM, RAM_REG, RAM_IMM8, RAM_RAM
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export class emulator{
    set timer(value: number) {
        this._timer = value;
    }
    private readonly ram: Uint16Array<ArrayBuffer>;
    private canvas: Canvas;
    private status_flags: StatusFlags;
    private register: Register;
    private pc: ProgramCounter;
    private readonly program: Uint16Array<ArrayBuffer>;
    private stop: boolean;
    private op: any;
    private _timer: number;

    constructor(canvas: HTMLCanvasElement,
                greater_element: HTMLElement, equal_element: HTMLElement, less_element: HTMLElement,
                register_id: HTMLElement[],
                program_counter_element: HTMLElement,
                program: Uint16Array<ArrayBuffer>) {

        this.ram = new Uint16Array(0xFFFF);
        this.canvas = new Canvas(canvas);
        this.status_flags = new StatusFlags(greater_element, equal_element, less_element);
        this.register = new Register(register_id);
        this.pc = new ProgramCounter(program_counter_element);
        this.program = program;
        this.stop = true;
        this.op= new Map<number, [any, number]>();
        this._timer = 10;

        let arith_data = [DATA.REG_REG, DATA.RAM_REG, DATA.REG_IMM8, DATA.REG_RAM, DATA.RAM_IMM8, DATA.RAM_RAM];
        let arith = [this.MOV, this.status_flags.CMP, this.ADD, this.SUB, this.MULT, this.DIV, this.QUOT, this.AND, this.OR, this.XOR, this.SHL, this.SHR, this.NEG, this.NOT];

        let one_data = [DATA.IMM8, DATA.REG, DATA.RAM];
        let one = [this.canvas.VID, this.canvas.VID_RED, this.canvas.VID_GREEN, this.canvas.VID_BLUE, this.canvas.VID_X, this.canvas.VID_Y];

        let jump = [this.pc.JMP, this.JEQ, this.JNE, this.JG, this.JLE, this.JL, this.JGE, this.CALL]

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

        for (const op in jump){
            this.op.set(i++, [op, DATA.IMM8]);

        }
        this.op.set(i++, [this.RTRN, DATA.None]);

    }

    async run(){
        while (this.stop) {
            await sleep(this._timer);
            let temp: number = this.program[this.pc.count * INSTRUCTION_BUS]!;
            let instruct: number = (temp >> 8);
            let reg1: number = temp & 0xF;
            let reg2: number = temp & 0xF0;

            let temp1 = this.op.get(instruct);
            let data_type:number = temp1[1];
            let operand: CallableFunction = temp1[0];

            let item1: number;
            let item2: number;
            let index: number;

            switch (data_type){
                case DATA.REG_REG:
                    item1 = this.register.getRegItem(reg1);
                    item2 = this.register.getRegItem(reg2);
                    operand(item1, item2, this.register.setRegItem.bind(reg1));
                    break;
                case DATA.REG_IMM8:
                    item1 = this.register.getRegItem(reg1);
                    this.pc.next();
                    item2 = this.program[this.pc.count * INSTRUCTION_BUS]!;
                    operand(item1, item2, this.register.setRegItem.bind(reg1));
                    break;
                case DATA.REG_RAM:
                    item1 = this.register.getRegItem(reg1);
                    this.pc.next();
                    item2 = this.ram[this.program[this.pc.count * INSTRUCTION_BUS]!]!;
                    operand(item1, item2, this.register.setRegItem.bind(reg1));
                    break;
                case DATA.RAM_REG:
                    item1 = this.register.getRegItem(reg1);
                    this.pc.next();
                    index = this.program[this.pc.count * INSTRUCTION_BUS]!;
                    item2 = this.ram[index]!;
                    operand(item1, item2, this.save_ram.bind(index));
                    break;
                case DATA.RAM_IMM8:
                    this.pc.next();
                    item1 = this.program[this.pc.count * INSTRUCTION_BUS]!;
                    this.pc.next();
                    index = this.program[this.pc.count * INSTRUCTION_BUS]!;
                    item2 = this.ram[index]!;
                    operand(item1, item2, this.save_ram.bind(index));
                    break;
                case DATA.RAM_RAM:
                    this.pc.next();
                    item1 = this.ram[this.program[this.pc.count * INSTRUCTION_BUS]!]!;
                    this.pc.next();
                    index = this.program[this.pc.count * INSTRUCTION_BUS!]!;
                    item2 = this.ram[index]!;
                    operand(item1, item2, this.save_ram.bind(index));
                    break;
                case DATA.REG:
                    item1 = this.register.getRegItem(reg1);
                    operand(item1);
                    break;
                case DATA.IMM8:
                    this.pc.next();
                    item1 = this.program[this.pc.count * INSTRUCTION_BUS]!;
                    operand(item1);
                    break;
                case DATA.RAM:
                    this.pc.next();
                    item1 = this.ram[this.program[this.pc.count * INSTRUCTION_BUS ]!]!;
                    operand(item1);
                    break;
                case DATA.None:
                    operand();
                    break;
            }
        }
    }

    save_ram(index: number, value: number){
        this.ram[index] = value;
    }


    MOV(value1:number, _value2:number, set: CallableFunction){set(value1);}
    ADD(value1:number, value2:number, set: CallableFunction){set(value1 + value2);}
    SUB(value1:number, value2:number, set: CallableFunction){set(value1 - value2);}
    MULT(value1:number, value2:number, set: CallableFunction){set(value1 * value2);}
    DIV(value1:number, value2:number, set: CallableFunction){
        if (value2 === 0)
            set(0);
        set(value1 - value2);
    }
    QUOT(value1:number, value2:number, set: CallableFunction){
        if (value2 === 0)
            set(0);
        set(value1 % value2);
    }
    AND(value1:number, value2:number, set: CallableFunction){set(value1 & value2);}
    OR(value1:number, value2:number, set: CallableFunction){set(value1 | value2);}
    XOR(value1:number, value2:number, set: CallableFunction){set(value1 ^ value2);}
    SHL(value1:number, value2:number, set: CallableFunction){set(value1 << value2);}
    SHR(value1:number, value2:number, set: CallableFunction){set(value1 >> value2);}

    JEQ(value:number){if (this.status_flags.equal) this.pc.JMP(value);}
    JNE(value:number){if (!this.status_flags.equal) this.pc.JMP(value);}
    JG(value:number){if (this.status_flags.greater) this.pc.JMP(value);}
    JLE(value:number){if (this.status_flags.less || this.status_flags.equal) this.pc.JMP(value);}
    JL(value:number){if (this.status_flags.less) this.pc.JMP(value);}
    JGE(value:number){if (this.status_flags.greater || this.status_flags.equal) this.pc.JMP(value);}
    CALL(value:number){
        // @ts-ignore
        this.ram[this.register.getRegItem(STACK_POINTER)]  = this.pc.JMP;
        this.pc.JMP(value);
    }
    RTRN(){
        this.pc.JMP(this.ram[this.register.getRegItem(STACK_POINTER)] as number);
    }

    NEG(value: number, set: CallableFunction){set(-value);}
    NOT(value: number, set: CallableFunction){set(~value);}
    NOP(){}
    HALT(){this.stop = false}
}

class Canvas {
    private ctx: CanvasRenderingContext2D;
    private readonly imageData: ImageData;
    private readonly data:  Uint8ClampedArray;
    private x!: number;
    private y!: number;
    private r!: number;
    private g!: number;
    private b!: number;

    constructor(canvas: HTMLCanvasElement) {
        // XTerm256 color model (8-bit)
        // using rgb555Data, a 16-bit integer containing RRRRR GGGGG BBBBB
        this.ctx = canvas.getContext('2d')!;
        this.imageData = this.ctx.createImageData(CANVAS_SIZE, CANVAS_SIZE);
        this.data = this.imageData.data;
        this.reset();
    }
    reset(){
        this.fill_back();
        this.x = 0;
        this.y = 0;
        this.r = 0;
        this.g = 0;
        this.b = 0;
    }
    set VID_X(val: number){ this.x = val & CANVAS_SIZE;}
    set VID_Y(val: number){ this.y = val & CANVAS_SIZE;}

    set VID_RED(val: number){ this.r = val & COLOR_SIZE * 4;}
    set VID_GREEN(val: number){ this.g = val & COLOR_SIZE * 4;}
    set VID_BLUE(val: number){ this.b = val & COLOR_SIZE * 4;}

    fill_back(){
        for (let y = 0; y < CANVAS_SIZE; y++) {
            for (let x = 0; x < CANVAS_SIZE; x++) {
                    const index = (y * CANVAS_SIZE + x) * 4;

                    // Set the color values (0-255)
                    this.data[index] = 0;         // Red
                    this.data[index + 1] = 0;     // Green
                    this.data[index + 2] = 0;     // Blue
                    this.data[index + 3] = 255;   // Alpha (opacity, 0-255)
            }
        }
        this.ctx.putImageData(this.imageData, 0, 0);
    }

    VID() {
        const index = (this.y * CANVAS_SIZE + this.x) * 4;

        // Set the color values (0-255)
        this.data[index] = this.r;          // Red
        this.data[index + 1] = this.g;      // Green
        this.data[index + 2] = this.b;      // Blue
        this.data[index + 3] = 255;         // Alpha (opacity, 0-255)

        this.ctx.putImageData(this.imageData, 0, 0);
    }
}

class StatusFlags{
    private _greater: boolean;
    private _equal: boolean;
    private _less: boolean;
    private greater_cell: HTMLElement;
    private equal_cell: HTMLElement;
    private less_cell: HTMLElement;

    constructor(greater_element: HTMLElement, equal_element: HTMLElement, less_element: HTMLElement) {
        this._greater = false;
        this._equal = false;
        this._less = false;
        this.greater_cell = greater_element;
        this.equal_cell = equal_element;
        this.less_cell = less_element;
        this.reset();
    }
    reset(){
        this.greater_cell.textContent = '0';
        this.equal_cell.textContent = '0';
        this.less_cell.textContent = '0';
    }
    get greater(): boolean {return this._greater;}
    get equal(): boolean {return this._equal;}
    get less(): boolean {return this._less;}

    CMP(value1:number, value2:number){
        let equal = value1 === value2;
        this.equal_cell.textContent = equal ? '1':'0';
        this._equal= equal;

        let greater = value1 <= value2;
        this.greater_cell.textContent = greater ? '1':'0';
        this._greater= greater;

        this.less_cell.textContent = greater ? '0':'1';
        this._less= !greater;
    }
}

class Register {
    private readonly reg: Int16Array<ArrayBuffer>;
    private readonly cells: HTMLElement[];
    constructor(cell_id: HTMLElement[]) {
        this.reg = new Int16Array(REG_SIZE);
        this.cells = cell_id;

        this.reset();
    }

    reset(){
        this.reg.fill(0);
        for (let i = 0; i <= REG_SIZE; i++){
            if (this.cells[i]) {
                this.cells[i]!.textContent = String(0);
            }
        }
    }
    setRegItem(index:number, value:number){
        this.reg[index] = value;
        this.cells[index]!.textContent = String(value);
    }

    getRegItem(index:number): number{
        return this.reg[index]!;
    }

}

class ProgramCounter {
    private pc_cell: HTMLElement;
    count!: number;

    constructor(pc_element:HTMLElement) {
        this.pc_cell = pc_element;
        this.pc_cell.textContent = String(0);
        this.reset();
    }
    reset(){
        this.pc_cell.textContent = String(0);
        this.count = 0;
    }
    JMP(value:number): void{
        this.pc_cell.textContent = String(value);
        this.count = value;
    }
    next(): void{
        this.count += 1;
        this.pc_cell.textContent = String(this.count);
    }
}


