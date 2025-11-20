import tkinter as tk
from tkinter import messagebox, scrolledtext
import time
import threading

class UniversalTuringMachine:
    def __init__(self, transitions, start_state, halt_states, tape):
        self.transitions = transitions
        self.start_state = start_state
        self.halt_states = halt_states
        self.reset(tape)

    def reset(self, tape):
        self.tape = list(tape) if tape else ['_']
        self.head = 0
        self.state = self.start_state
        self.steps = 0
        self.running = False

    def step(self):
        if self.state in self.halt_states:
            return f"✅ Halted in state {self.state}"
        symbol = self.tape[self.head] if self.head < len(self.tape) else '_'
        key = (self.state, symbol)
        if key not in self.transitions:
            return f"⚠️ No rule for ({self.state}, {symbol}) — Halting."

        new_state, write_symbol, move = self.transitions[key]
        self.tape[self.head] = write_symbol
        self.state = new_state

        if move == 'R':
            self.head += 1
            if self.head >= len(self.tape):
                self.tape.append('_')
        elif move == 'L':
            if self.head == 0:
                self.tape.insert(0, '_')
            else:
                self.head -= 1

        self.steps += 1
        return f"({key[0]}, {key[1]}) -> ({new_state}, {write_symbol}, {move})"


def parse_rules(rules_text):
    transitions = {}
    for line in rules_text.strip().split('\n'):
        if not line.strip() or line.strip().startswith('#'):
            continue
        left, right = line.split('->')
        current_state, read_symbol = [s.strip() for s in left.split(',')]
        new_state, write_symbol, move = [s.strip() for s in right.split(',')]
        transitions[(current_state, read_symbol)] = (new_state, write_symbol, move.upper())
    return transitions


# --- GUI Setup ---
class TuringGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal Turing Machine Simulator (Python GUI)")
        self.root.geometry("900x600")
        self.root.config(bg="#f8fafc")

        # Machine
        self.machine = None
        self.running = False

        # Layout
        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.root, text="Universal Turing Machine Simulator", font=("Helvetica", 18, "bold"), bg="#f8fafc").pack(pady=10)

        frame = tk.Frame(self.root, bg="#f8fafc")
        frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Left panel
        config_frame = tk.Frame(frame, bg="#ffffff", relief="groove", bd=2)
        config_frame.pack(side="left", fill="y", padx=10, pady=10)

        tk.Label(config_frame, text="Transition Rules", bg="#ffffff", font=("Arial", 10, "bold")).pack(pady=4)
        self.rules_text = scrolledtext.ScrolledText(config_frame, width=40, height=10)
        self.rules_text.insert(tk.END, "q0,1 -> q0,1,R\nq0,0 -> q0,0,R\nq0,_ -> q1,_,L\nq1,1 -> q1,0,L\nq1,0 -> q_accept,1,L\nq1,_ -> q_accept,1,L")
        self.rules_text.pack(padx=5, pady=5)

        tk.Label(config_frame, text="Initial Tape", bg="#ffffff").pack()
        self.tape_entry = tk.Entry(config_frame)
        self.tape_entry.insert(0, "1011")
        self.tape_entry.pack(pady=2)

        tk.Label(config_frame, text="Start State", bg="#ffffff").pack()
        self.start_entry = tk.Entry(config_frame)
        self.start_entry.insert(0, "q0")
        self.start_entry.pack(pady=2)

        tk.Label(config_frame, text="Halt States (comma separated)", bg="#ffffff").pack()
        self.halt_entry = tk.Entry(config_frame)
        self.halt_entry.insert(0, "q_accept,q_reject")
        self.halt_entry.pack(pady=2)

        # Buttons
        btn_frame = tk.Frame(config_frame, bg="#ffffff")
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Load Machine", bg="#2563eb", fg="white", command=self.load_machine, width=15).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(btn_frame, text="Step", bg="#f59e0b", fg="white", command=self.step_machine, width=10).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Run", bg="#16a34a", fg="white", command=self.run_machine, width=10).grid(row=1, column=0, padx=5)
        tk.Button(btn_frame, text="Reset", bg="#dc2626", fg="white", command=self.reset_machine, width=10).grid(row=1, column=1, padx=5)

        # Right panel
        right_frame = tk.Frame(frame, bg="#ffffff", relief="groove", bd=2)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        tk.Label(right_frame, text="Tape Visualization", bg="#ffffff", font=("Arial", 10, "bold")).pack(pady=5)
        self.tape_display = tk.Label(right_frame, text="", bg="#ffffff", font=("Courier", 14))
        self.tape_display.pack(pady=5)

        tk.Label(right_frame, text="Log Output", bg="#ffffff", font=("Arial", 10, "bold")).pack(pady=5)
        self.log_output = scrolledtext.ScrolledText(right_frame, width=60, height=15, bg="#111827", fg="#e5e7eb", font=("Courier", 10))
        self.log_output.pack(padx=10, pady=10)

    def load_machine(self):
        try:
            transitions = parse_rules(self.rules_text.get("1.0", tk.END))
            start_state = self.start_entry.get().strip()
            halt_states = [x.strip() for x in self.halt_entry.get().split(',')]
            tape = self.tape_entry.get().strip()

            if not start_state or not halt_states:
                raise ValueError("Start and Halt states must be defined.")

            self.machine = UniversalTuringMachine(transitions, start_state, halt_states, tape)
            self.update_tape()
            self.log("✅ Machine Loaded Successfully.\n")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load machine: {e}")

    def step_machine(self):
        if not self.machine:
            return messagebox.showwarning("Warning", "Load the machine first!")
        msg = self.machine.step()
        self.update_tape()
        self.log(msg)

    def run_machine(self):
        if not self.machine:
            return messagebox.showwarning("Warning", "Load the machine first!")
        if self.running:
            self.running = False
            return
        self.running = True
        threading.Thread(target=self.run_loop).start()

    def run_loop(self):
        while self.running:
            msg = self.machine.step()
            self.update_tape()
            self.log(msg)
            if "Halt" in msg or "⚠️" in msg:
                self.running = False
                break
            time.sleep(0.5)

    def reset_machine(self):
        if not self.machine:
            return
        self.machine.reset(self.tape_entry.get().strip())
        self.update_tape()
        self.log("🔁 Machine Reset.\n")

    def update_tape(self):
        if not self.machine:
            return
        tape_display = ""
        for i, sym in enumerate(self.machine.tape):
            if i == self.machine.head:
                tape_display += f"[{sym}]"
            else:
                tape_display += f" {sym} "
        self.tape_display.config(text=tape_display)

    def log(self, message):
        self.log_output.insert(tk.END, message + "\n")
        self.log_output.see(tk.END)


# --- Run GUI ---
if __name__ == "__main__":
    root = tk.Tk()
    app = TuringGUI(root)
    root.mainloop()
