import tkinter as tk
from tkinter import filedialog, Frame, Label, Button, Radiobutton, OptionMenu, StringVar, BooleanVar, PhotoImage
import os
from pathlib import Path
import webbrowser  # For opening links

def gui_prompt_for_inputs():
    root = tk.Tk()
    root.title("MultiLGraphWiki")
    root.geometry("550x700")  # Increased height to accommodate layout changes
    root.configure(bg="#F5F5F5")

    text_color = "#222222"
    highlight_color = "#0072B2"
    button_color_start = "#009E73"  # Green (Start Processing)
    button_color_github = "#0072B2"  # Blue (GitHub)
    button_color_contact = "#D55E00"  # Orange (Contact Dev)
    button_text_color = "#FFFFFF"
    dropdown_bg = "#D3D3D3"
    radio_select_color = "#F5F5F5"

    title_label = Label(root, text="MultiLGraphWiki", font=("Arial", 18, "bold"), bg="#F5F5F5", fg=highlight_color)
    title_label.pack(pady=(20, 5))

    subtitle_label = Label(root, text="Wikipedia XML Dump Processing Tool", font=("Arial", 12), bg="#F5F5F5", fg=text_color)
    subtitle_label.pack(pady=(0, 20))

    main_frame = Frame(root, bg="#F5F5F5", padx=40, pady=10)
    main_frame.pack(fill="both", expand=True)

    dump_filepath = None
    selected_language = StringVar(root)
    generate_graph_flag = BooleanVar(value=True)
    base_dir = None

    # -----------------------------
    # Step 1: Select Dump File
    # -----------------------------
    step1_label = Label(main_frame, text="Step 1: Select Compressed XML Dump File", font=("Arial", 12, "bold"),
                        bg="#F5F5F5", fg=highlight_color, anchor="w")
    step1_label.pack(fill="x", pady=(10, 5))

    def select_dump_file():
        nonlocal dump_filepath
        selected_file = filedialog.askopenfilename(
            title="Select the compressed XML dump file",
            filetypes=[("BZ2 files", "*.bz2"), ("All files", "*.*")]
        )
        if selected_file:
            dump_filepath = Path(selected_file)
            dump_file_label.config(text=f"Selected: {dump_filepath.name}")

    dump_button = Button(main_frame, text="Browse...", command=select_dump_file,
                         bg=button_color_start, fg=button_text_color, width=15)
    dump_button.pack(anchor="w", pady=(0, 5))

    dump_file_label = Label(main_frame, text="No file selected", bg="#F5F5F5", fg=text_color)
    dump_file_label.pack(anchor="w", pady=(0, 10))

    # ------------------------
    # Step 2: Select Language
    # ------------------------
    step2_label = Label(main_frame, text="Step 2: Select Language", font=("Arial", 12, "bold"),
                        bg="#F5F5F5", fg=highlight_color, anchor="w")
    step2_label.pack(fill="x", pady=(10, 5))

    available_languages = ['en', 'es', 'el', 'pl', 'it', 'nl', 'eu', 'hi', 'de']
    selected_language.set(available_languages[0])

    language_frame = Frame(main_frame, bg="#F5F5F5")
    language_frame.pack(fill="x", pady=(0, 10))

    language_label = Label(language_frame, text="Language:", bg="#F5F5F5", fg=text_color)
    language_label.pack(side="left", padx=(0, 10))

    dropdown = OptionMenu(language_frame, selected_language, *available_languages)
    dropdown.config(bg=dropdown_bg, fg=text_color, width=5)
    dropdown.pack(side="left")

    # -------------------------
    # Step 3: Generate Graph?
    # -------------------------
    step3_label = Label(main_frame, text="Step 3: Generate Graph", font=("Arial", 12, "bold"),
                        bg="#F5F5F5", fg=highlight_color, anchor="w")
    step3_label.pack(fill="x", pady=(10, 5))

    graph_frame = Frame(main_frame, bg="#F5F5F5")
    graph_frame.pack(fill="x", pady=(0, 10))

    yes_radio = Radiobutton(graph_frame, text="Yes", variable=generate_graph_flag, value=True,
                            bg="#F5F5F5", fg=text_color, selectcolor=radio_select_color)
    yes_radio.pack(side="left", padx=(0, 10))

    no_radio = Radiobutton(graph_frame, text="No", variable=generate_graph_flag, value=False,
                           bg="#F5F5F5", fg=text_color, selectcolor=radio_select_color)
    no_radio.pack(side="left")

    # -----------------------------
    # Step 4: Select Output Folder
    # -----------------------------
    step4_label = Label(main_frame, text="Step 4: Select Output Directory", font=("Arial", 12, "bold"),
                        bg="#F5F5F5", fg=highlight_color, anchor="w")
    step4_label.pack(fill="x", pady=(10, 5))

    def select_output_dir():
        nonlocal base_dir
        selected_dir = filedialog.askdirectory(title="Select the output directory")
        if selected_dir:
            base_dir = Path(selected_dir)
            dir_label.config(text=f"Selected: {base_dir}")

    dir_button = Button(main_frame, text="Browse...", command=select_output_dir,
                        bg=button_color_start, fg=button_text_color, width=15)
    dir_button.pack(anchor="w", pady=(0, 5))

    dir_label = Label(main_frame, text="No directory selected", bg="#F5F5F5", fg=text_color)
    dir_label.pack(anchor="w", pady=(0, 10))

    # -----------------------
    # Bottom Buttons Section
    # -----------------------
    
    # Function to open the GitHub repository
    def open_github():
        webbrowser.open("https://github.com/YOUR_REPOSITORY_URL_HERE")

    # Function to contact the developer
    def contact_developer():
        webbrowser.open("mailto:developer@example.com?subject=MultiLGraphWiki%20Support")

    # The "Start Processing" button (Centered)
    confirm_button = Button(root, text="Start Processing", font=("Arial", 12, "bold"),
                            bg=button_color_start, fg=button_text_color, width=20, command=root.quit)
    confirm_button.pack(pady=(10, 5))

    # Frame to hold the two lower buttons
    lower_buttons_frame = Frame(root, bg="#F5F5F5")
    lower_buttons_frame.pack(pady=(5, 10))

    # Button to open GitHub repository (Left)
    github_button = Button(lower_buttons_frame, text="GitHub Repo", font=("Arial", 12),
                           bg=button_color_github, fg=button_text_color, width=15, command=open_github)
    github_button.pack(side="left", padx=40)

    # Button to contact the developer (Right)
    contact_button = Button(lower_buttons_frame, text="Contact Dev", font=("Arial", 12),
                            bg=button_color_contact, fg=button_text_color, width=15, command=contact_developer)
    contact_button.pack(side="right", padx=40)

    error_label = Label(root, text="", fg="#D55E00", bg="#F5F5F5", font=("Arial", 10))
    error_label.pack(pady=(0, 10))

    # -----------------------
    # Optional: Logo Display
    # -----------------------
    try:
        logo_path = "logo/mestizajes_logo-removebg-preview.png"
        if os.path.exists(logo_path):
            logo_image = PhotoImage(file=logo_path)
            logo_label = Label(root, image=logo_image, bg="#F5F5F5")
            logo_label.pack(pady=(10, 20))
            logo_label.image = logo_image  # Keep reference
    except Exception as e:
        print(f"Error loading logo: {e}")

    root.mainloop()
    return dump_filepath, selected_language.get(), base_dir, generate_graph_flag.get()