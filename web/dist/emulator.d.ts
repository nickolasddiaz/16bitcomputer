export declare class emulator {
    set timer(value: number);
    private readonly ram;
    private canvas;
    private status_flags;
    private register;
    private pc;
    private readonly program;
    private stop;
    private op;
    private _timer;
    constructor(canvas: HTMLCanvasElement, greater_element: HTMLElement, equal_element: HTMLElement, less_element: HTMLElement, register_id: HTMLElement[], program_counter_element: HTMLElement, program: Uint16Array<ArrayBuffer>);
    run(): Promise<void>;
    save_ram(index: number, value: number): void;
    MOV(value1: number, _value2: number, set: CallableFunction): void;
    ADD(value1: number, value2: number, set: CallableFunction): void;
    SUB(value1: number, value2: number, set: CallableFunction): void;
    MULT(value1: number, value2: number, set: CallableFunction): void;
    DIV(value1: number, value2: number, set: CallableFunction): void;
    QUOT(value1: number, value2: number, set: CallableFunction): void;
    AND(value1: number, value2: number, set: CallableFunction): void;
    OR(value1: number, value2: number, set: CallableFunction): void;
    XOR(value1: number, value2: number, set: CallableFunction): void;
    SHL(value1: number, value2: number, set: CallableFunction): void;
    SHR(value1: number, value2: number, set: CallableFunction): void;
    JEQ(value: number): void;
    JNE(value: number): void;
    JG(value: number): void;
    JLE(value: number): void;
    JL(value: number): void;
    JGE(value: number): void;
    CALL(value: number): void;
    RTRN(): void;
    NEG(value: number, set: CallableFunction): void;
    NOT(value: number, set: CallableFunction): void;
    NOP(): void;
    HALT(): void;
}
//# sourceMappingURL=emulator.d.ts.map