import psutil
import tkinter as tk
import customtkinter as ctk
import threading
import time
import os
import my_module

# -----------------------------
# Thread wrapper to track stats
# -----------------------------
def run_thread(name, func, arg, text_widget, progress_var, status_label):
    start_time = time.perf_counter()  # high-resolution timer
    thread_id = threading.get_native_id()
    pid = os.getpid()
    text_widget.insert(tk.END, f"[{name}] Started. Thread ID: {thread_id}, PID: {pid}\n")
    text_widget.see(tk.END)
    status_label.configure(text=f"{name} Running...")

    result_container = [None]
    finished = [False]

    def worker():
        result_container[0] = func(arg)
        finished[0] = True

    t = threading.Thread(target=worker)
    t.start()

    # Animate progress bar while running
    direction = 0.01
    while not finished[0]:
        current = progress_var.get()
        if current >= 0.9:
            direction = -0.01
        elif current <= 0.1:
            direction = 0.01
        progress_var.set(current + direction)
        time.sleep(0.05)

    t.join()
    progress_var.set(1.0)
    runtime = time.perf_counter() - start_time
    process = psutil.Process(pid)
    mem_info = process.memory_info()
    text_widget.insert(tk.END,
                       f"[{name}] Finished. Result: {result_container[0]}, Runtime: {runtime:.4f}s, RAM: {mem_info.rss / 1024**2:.2f} MB\n")
    text_widget.see(tk.END)
    status_label.configure(text=f"{name} Finished")


# -----------------------------
# GUI setup
# -----------------------------
def establish_gui():
    ctk.set_appearance_mode("dark")  # dark mode for modern look
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.geometry("900x600")
    app.title("GPU vs CPU Virtual Benchmarking")

    # Top Frame: Title
    top_frame = ctk.CTkFrame(app, corner_radius=12)
    top_frame.pack(fill="x", padx=20, pady=10)
    title_label = ctk.CTkLabel(top_frame, text="GPU vs CPU Benchmarking Dashboard",
                               font=ctk.CTkFont(size=22, weight="bold"),
                               text_color="#9A89CF")
    title_label.pack(pady=10)

    # Middle Frame: Text Log
    middle_frame = ctk.CTkFrame(app, corner_radius=12)
    middle_frame.pack(fill="both", expand=True, padx=20, pady=10)
    scrollable_frame = ctk.CTkScrollableFrame(middle_frame)
    scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
    text_box = tk.Text(scrollable_frame, height=15, bg="#08565B", fg="#FFFFFF")
    text_box.pack(fill="both", expand=True)

    # Bottom Frame: Progress Bars & Buttons
    bottom_frame = ctk.CTkFrame(app, corner_radius=12)
    bottom_frame.pack(fill="x", padx=20, pady=10)

    # Threads info
    threads_info = [("GNFS_small", 12345, my_module.GNFS_small),
                    ("Shors", 34, my_module.Shors)]
    progress_vars = []
    status_labels = []

    for name, _, _ in threads_info:
        label = ctk.CTkLabel(bottom_frame, text=f"{name} Progress", font=ctk.CTkFont(size=14))
        label.pack(pady=(10, 2))
        var = tk.DoubleVar(value=0.1)
        bar = ctk.CTkProgressBar(bottom_frame, variable=var, progress_color="#7A84A3")
        bar.pack(fill="x", padx=20, pady=(0, 5))
        progress_vars.append(var)

        status = ctk.CTkLabel(bottom_frame, text="Idle", text_color="#8D5F8D")
        status.pack(pady=(0, 5))
        status_labels.append(status)

    # Start threads button
    def start_threads():
        # Reset progress bars
        for var in progress_vars:
            var.set(0.1)
        text_box.insert(tk.END, "\n=== Starting new run ===\n")
        text_box.see(tk.END)
        for i, (name, arg, func) in enumerate(threads_info):
            threading.Thread(target=run_thread,
                             args=(name, func, arg, text_box, progress_vars[i], status_labels[i])).start()

    start_button = ctk.CTkButton(bottom_frame, text="Start Threads",
                                 fg_color="#7498BD",
                                 hover_color="#153658",
                                 corner_radius=12,
                                 font=ctk.CTkFont(size=16),
                                 command=start_threads)
    start_button.pack(pady=15)

    return app


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    app = establish_gui()
    app.mainloop()