import tkinter as tk
from tkinter import filedialog, Frame, Label, Button, Radiobutton, OptionMenu, StringVar, BooleanVar
import os
from pathlib import Path


def gui_prompt_for_inputs():
    """
    Launches a GUI to collect user inputs for processing Wikipedia XML dumps.

    Returns:
        tuple: Contains the selected file path (Path), language (str), base directory (Path), 
        and a flag indicating whether to generate a graph (bool).
    """
    root = tk.Tk()
    root.title("MultiLGraphWiki")
    root.geometry("550x600")
    root.configure(bg="#F5F5F5")  # neutral light grey background

    # colorblind-friendly palette
    text_color = "#222222"
    highlight_color = "#0072B2"
    button_color = "#009E73"
    button_text_color = "#FFFFFF"
    dropdown_bg = "#D3D3D3"
    radio_select_color = "#F5F5F5"

    # application title
    title_label = Label(root, text="MultiLGraphWiki",
                        font=("Arial", 18, "bold"), bg="#F5F5F5", fg=highlight_color)
    title_label.pack(pady=(20, 5))

    subtitle_label = Label(root, text="Wikipedia XML Dump Processing Tool",
                           font=("Arial", 12), bg="#F5F5F5", fg=text_color)
    subtitle_label.pack(pady=(0, 20))

    # create main frame for inputs
    main_frame = Frame(root, bg="#F5F5F5", padx=40, pady=10)
    main_frame.pack(fill="both", expand=True)

    dump_filepath = None
    selected_language = StringVar(root)
    generate_graph_flag = BooleanVar(value=True)
    base_dir = None

    # step 1: select XML dump file
    step1_label = Label(main_frame, text="Step 1: Select Compressed XML Dump File",
                        font=("Arial", 12, "bold"), bg="#F5F5F5", fg=highlight_color, anchor="w")
    step1_label.pack(fill="x", pady=(10, 5))

    def select_dump_file():
        """Opens file dialog to select a Wikipedia dump file."""
        nonlocal dump_filepath
        selected_file = filedialog.askopenfilename(
            title="Select the compressed XML dump file",
            filetypes=[("BZ2 files", "*.bz2"), ("All files", "*.*")]
        )
        if selected_file:
            dump_filepath = Path(selected_file)
            dump_file_label.config(text=f"Selected: {dump_filepath.name}")

    dump_button = Button(main_frame, text="Browse...", command=select_dump_file,
                         bg=button_color, fg=button_text_color, width=15)
    dump_button.pack(anchor="w", pady=(0, 5))

    dump_file_label = Label(main_frame, text="No file selected",
                            bg="#F5F5F5", fg=text_color)
    dump_file_label.pack(anchor="w", pady=(0, 10))

    # step 2: select language
    step2_label = Label(main_frame, text="Step 2: Select Language",
                        font=("Arial", 12, "bold"), bg="#F5F5F5", fg=highlight_color, anchor="w")
    step2_label.pack(fill="x", pady=(10, 5))

    available_languages = ['en', 'es', 'el', 'pl', 'it', 'nl', 'eu', 'hi', 'de']
    selected_language.set(available_languages[0])

    language_frame = Frame(main_frame, bg="#F5F5F5")
    language_frame.pack(fill="x", pady=(0, 10))

    language_label = Label(language_frame, text="Language:",
                           bg="#F5F5F5", fg=text_color)
    language_label.pack(side="left", padx=(0, 10))

    dropdown = OptionMenu(language_frame, selected_language, *available_languages)
    dropdown.config(bg=dropdown_bg, fg=text_color, width=5)
    dropdown.pack(side="left")

    # step 3: generate graph option
    step3_label = Label(main_frame, text="Step 3: Generate Graph",
                        font=("Arial", 12, "bold"), bg="#F5F5F5", fg=highlight_color, anchor="w")
    step3_label.pack(fill="x", pady=(10, 5))

    graph_frame = Frame(main_frame, bg="#F5F5F5")
    graph_frame.pack(fill="x", pady=(0, 10))

    yes_radio = Radiobutton(graph_frame, text="Yes", variable=generate_graph_flag,
                            value=True, bg="#F5F5F5", fg=text_color, selectcolor=radio_select_color)
    yes_radio.pack(side="left", padx=(0, 10))

    no_radio = Radiobutton(graph_frame, text="No", variable=generate_graph_flag,
                           value=False, bg="#F5F5F5", fg=text_color, selectcolor=radio_select_color)
    no_radio.pack(side="left")

    # step 4: select output directory
    step4_label = Label(main_frame, text="Step 4: Select Output Directory",
                        font=("Arial", 12, "bold"), bg="#F5F5F5", fg=highlight_color, anchor="w")
    step4_label.pack(fill="x", pady=(10, 5))

    def select_output_dir():
        """Opens directory selection dialog for output location."""
        nonlocal base_dir
        selected_dir = filedialog.askdirectory(title="Select the output directory")
        if selected_dir:
            base_dir = Path(selected_dir)
            dir_label.config(text=f"Selected: {base_dir}")

    dir_button = Button(main_frame, text="Browse...", command=select_output_dir,
                        bg=button_color, fg=button_text_color, width=15)
    dir_button.pack(anchor="w", pady=(0, 5))

    dir_label = Label(main_frame, text="No directory selected",
                      bg="#F5F5F5", fg=text_color)
    dir_label.pack(anchor="w", pady=(0, 10))

    # confirm button
    def confirm_selection():
        """Validates user inputs and exits the GUI if selections are complete."""
        if dump_filepath and base_dir:
            root.quit()
        else:
            error_label.config(text="Please complete all required fields.")

    confirm_button = Button(root, text="Start Processing", font=("Arial", 12, "bold"),
                            bg=button_color, fg=button_text_color, width=20, command=confirm_selection)
    confirm_button.pack(pady=(10, 5))

    # error label
    error_label = Label(root, text="", fg="#D55E00", bg="#F5F5F5", font=("Arial", 10))
    error_label.pack(pady=(0, 10))

    root.mainloop()
    root.destroy()

    return dump_filepath, selected_language.get(), base_dir, generate_graph_flag.get()