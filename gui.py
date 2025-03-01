import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import multiprocessing

def gui_prompt_for_inputs():
    root = tk.Tk()
    root.title("MultiLGraphWiki - XML Dump Processing")
    root.geometry("500x600")  # Adjusted height
    root.configure(bg="#F5F5F5")

    # Attempt to load a logo (optional, repositioned to bottom-right)
    logo_path = "logo/mestizajes_logo-removebg-preview.png"
    try:
        logo = tk.PhotoImage(file=str(logo_path))
        logo_label = tk.Label(root, image=logo, bg="#F5F5F5")
        logo_label.place(relx=0.85, rely=0.85, anchor="center")
    except Exception as e:
        print(f"Error loading logo: {e}")

    # Algorithm Name in Monaco Font
    tk.Label(
        root, text="MultiLGraphWiki", font=("Monaco", 16, "bold"),
        bg="#F5F5F5", fg="#222222"
    ).pack(pady=(10, 5))

    text_color = "#222222"
    highlight_color = "#0072B2"
    button_color = "#009E73"
    button_text_color = "#FFFFFF"

    tk.Label(root, text="Step 1: Select Compressed XML Dump File",
             font=("Arial", 12, "bold"), bg="#F5F5F5", fg=highlight_color).pack(pady=(10, 5))
    dump_filepath = filedialog.askopenfilename(title="Select XML dump file",
                                               filetypes=[("BZ2 files", "*.bz2"), ("All files", "*.*")])
    dump_filepath = Path(dump_filepath) if dump_filepath else None

    tk.Label(root, text="Step 2: Select Base Directory for Output Files",
             font=("Arial", 12, "bold"), bg="#F5F5F5", fg=highlight_color).pack(pady=(10, 5))
    base_dir = filedialog.askdirectory(title="Select base directory")
    base_dir = Path(base_dir) if base_dir else None

    language_frame = tk.Frame(root, bg="#F5F5F5")
    language_frame.pack(pady=(10, 5), padx=20, fill="x")
    tk.Label(language_frame, text="Step 3: Select Your Language",
             font=("Arial", 12, "bold"), bg="#F5F5F5", fg=highlight_color).pack(anchor="w")
    selected_language = tk.StringVar(root)
    available_languages = ['EN', 'ES', 'GR', 'PL', 'IT', 'NL', 'EUS', 'HI', 'DE']
    selected_language.set(available_languages[0])
    dropdown = tk.OptionMenu(language_frame, selected_language, *available_languages)
    dropdown.config(bg="#D3D3D3", fg=text_color, font=("Arial", 10))
    dropdown.pack(pady=5)

    graph_frame = tk.Frame(root, bg="#F5F5F5")
    graph_frame.pack(pady=(10, 5), padx=20, fill="x")
    tk.Label(graph_frame, text="Step 4: Generate Graph?",
             font=("Arial", 12, "bold"), bg="#F5F5F5", fg=highlight_color).pack(anchor="w")
    generate_graph_flag = tk.BooleanVar()
    tk.Radiobutton(graph_frame, text="Yes", variable=generate_graph_flag, value=True,
                   bg="#F5F5F5", fg=text_color, selectcolor="#D3D3D3").pack(anchor="w")
    tk.Radiobutton(graph_frame, text="No", variable=generate_graph_flag, value=False,
                   bg="#F5F5F5", fg=text_color, selectcolor="#D3D3D3").pack(anchor="w")

    cpu_frame = tk.Frame(root, bg="#F5F5F5")
    cpu_frame.pack(pady=(10, 5), padx=20, fill="x")
    tk.Label(cpu_frame, text="Step 5: Number of CPU cores to use",
             font=("Arial", 12, "bold"), bg="#F5F5F5", fg=highlight_color).pack(anchor="w")
    available_cores = multiprocessing.cpu_count()
    num_cores_var = tk.IntVar(value=1)
    tk.Spinbox(cpu_frame, from_=1, to=available_cores, textvariable=num_cores_var,
               width=5, font=("Arial", 10)).pack(pady=5, anchor="w")

    def confirm_selection():
        chosen_cores = num_cores_var.get()
        if chosen_cores > available_cores:
            messagebox.showerror("Error", f"You requested {chosen_cores} cores, but only {available_cores} are available.")
            return
        root.quit()

    tk.Button(root, text="Confirm Selection", font=("Arial", 12),
              bg=button_color, fg=button_text_color, command=confirm_selection).pack(pady=(15, 10))

    root.mainloop()
    root.destroy()

    return dump_filepath, base_dir, selected_language.get(), generate_graph_flag.get(), num_cores_var.get()