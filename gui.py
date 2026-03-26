import tkinter as tk
from tkinter import filedialog, Frame, Label, Button, Radiobutton, OptionMenu, StringVar, BooleanVar, PhotoImage
import os
from pathlib import Path
import webbrowser  # For opening links

def gui_prompt_for_inputs():
    """
    Launches a Tkinter-based GUI to prompt for user inputs:
      1) Wikipedia dump file path,
      2) Output directory,
      3) Language code,
      4) Whether or not to generate a graph,

    Returns:
        (dump_filepath, selected_language, base_dir, generate_graph_flag):
        A tuple containing the file path of the Wikipedia dump, the selected language,
        the output directory, a boolean to indicate whether to generate a graph,
    """
    root = tk.Tk()
    root.title("WikiTextGraph")
    root.geometry("550x750")  # ensure everything fits without resizing

    # revert to the previous color scheme that worked on macOS
    # cross-platform safe color scheme
    system_bg = "white" # safe, neutral background
    text_color = "black" # high contrast text
    highlight_color = "blue" # standard heading highlight
    button_color_start = "lightgray" # replaces SystemButtonFace
    button_color_github = "lightgray"
    button_color_contact = "lightgray"
    button_text_color = "black"

    root.configure(bg=system_bg)
    root.columnconfigure(0, weight=1)  # allow column expansion
    
    def on_start():
        """
        Callback for the "Start Processing" button. Validates user inputs and
        closes the GUI if everything is set.
        """
        nonlocal dump_filepath, base_dir  # ensure modifications persist outside function
        
        if not dump_filepath or not base_dir:
            tk.messagebox.showwarning("Missing Input", "Please select both a dump file and an output directory before proceeding.")
            return  # prevent closing if inputs are missing

        # quit the main loop and destroy the GUI
        root.quit()
        root.destroy()


    # title
    title_label = Label(root, text="WikiTextGraph", font=("Arial", 18, "bold"), bg=system_bg, fg=highlight_color)
    title_label.grid(row=0, column=0, pady=(10, 5), sticky="ew")

    subtitle_label = Label(root, text="Wikipedia XML Dump Processing Tool", font=("Arial", 12), bg=system_bg, fg=text_color)
    subtitle_label.grid(row=1, column=0, pady=(0, 5), sticky="ew")

    # load Logo
    try:
        logo_path = "logo/mestizajes_logo-removebg-preview.png"
        if os.path.exists(logo_path):
            logo_img = PhotoImage(file=logo_path).subsample(3, 3)  # reduce size
            logo_label = Label(root, image=logo_img, bg=system_bg)
            logo_label.grid(row=2, column=0, pady=(0, 2), sticky="n")
            logo_label.image = logo_img  # keep reference

            # funding acknowledgment text
            funding_label = Label(root, text="Funded by Mestizajes", font=("Arial", 10, "italic"), bg=system_bg, fg=text_color)
            funding_label.grid(row=3, column=0, pady=(0, 10), sticky="n")
    except Exception as e:
        print(f"Error loading logo: {e}")

    main_frame = Frame(root, bg=system_bg)
    main_frame.grid(row=4, column=0, padx=40, pady=10, sticky="nsew")

    dump_filepath = None
    selected_language = StringVar(root)
    generate_graph_flag = BooleanVar(value=True)
    base_dir = None

    # step 1: Select Dump File
    step1_label = Label(main_frame, text="Step 1: Select Compressed XML Dump File", font=("Arial", 12, "bold"), bg=system_bg, fg=highlight_color, anchor="w")
    step1_label.grid(row=0, column=0, sticky="w", pady=(10, 5))

    def select_dump_file():
        """
        Opens a file dialog for the user to select a compressed Wikipedia XML dump
        (typically .bz2).
        """
        nonlocal dump_filepath
        selected_file = filedialog.askopenfilename(title="Select the compressed XML dump file", filetypes=[("BZ2 files", "*.bz2"), ("All files", "*.*")])
        if selected_file:
            dump_filepath = Path(selected_file)
            dump_file_label.config(text=f"Selected: {dump_filepath.name}")

    dump_button = Button(main_frame, text="Browse...", command=select_dump_file, bg=button_color_start, fg=button_text_color, width=15)
    dump_button.grid(row=1, column=0, sticky="w", pady=(0, 5))

    dump_file_label = Label(main_frame, text="No file selected", bg=system_bg, fg=text_color)
    dump_file_label.grid(row=2, column=0, sticky="w", pady=(0, 10))

    # step 2: Select Language
    step2_label = Label(main_frame, text="Step 2: Select Language", font=("Arial", 12, "bold"), bg=system_bg, fg=highlight_color, anchor="w")
    step2_label.grid(row=3, column=0, sticky="w", pady=(10, 5))

    available_languages = sorted(["en", "es", "el", "pl", "it", "nl", "eu", "hi", "de", "vi", "uk"])
    selected_language.set(available_languages[0])

    dropdown = OptionMenu(main_frame, selected_language, *available_languages)
    dropdown.grid(row=4, column=0, sticky="w")

    # step 3: Generate Graph (optional)
    step3_label = Label(main_frame, text="Step 3: Generate Graph", font=("Arial", 12, "bold"), bg=system_bg, fg=highlight_color, anchor="w")
    step3_label.grid(row=5, column=0, sticky="w", pady=(10, 5))

    yes_radio = Radiobutton(main_frame, text="Yes", variable=generate_graph_flag, value=True, bg=system_bg, fg=text_color)
    yes_radio.grid(row=6, column=0, padx=(0, 10), sticky="w")

    no_radio = Radiobutton(main_frame, text="No", variable=generate_graph_flag, value=False, bg=system_bg, fg=text_color)
    no_radio.grid(row=6, column=1, sticky="w")
    
    # string2id_label = Label(main_frame, text="Node Label Format", font=("Arial", 12, "bold"), bg=system_bg, fg=highlight_color, anchor="w")
    # string2id_label.grid(row=7, column=0, sticky="w", pady=(10, 5))

    # use_string_labels = BooleanVar(value=False)
    # label_option = tk.Checkbutton(main_frame,
                                  # text="Keep node labels as strings instead of replacing them with numeric IDs",
                                  # variable=use_string_labels,
                                 #  onvalue=True, offvalue=False,
                                 #  bg=system_bg, fg=text_color)
    # label_option.grid(row=8, column=0, sticky="w", pady=(0, 10))

    # step 4: Select Output Folder
    step4_label = Label(main_frame, text="Step 4: Select Output Directory", font=("Arial", 12, "bold"), bg=system_bg, fg=highlight_color, anchor="w")
    step4_label.grid(row=7, column=0, sticky="w", pady=(10, 5))

    def select_output_dir():
        """
        Opens a directory dialog for the user to choose a base output directory.
        """
        nonlocal base_dir
        selected_dir = filedialog.askdirectory(title="Select the output directory")
        if selected_dir:
            base_dir = Path(selected_dir)
            dir_label.config(text=f"Selected: {base_dir}")

    dir_button = Button(main_frame, text="Browse...", command=select_output_dir, bg=button_color_start, fg=button_text_color, width=15)
    dir_button.grid(row=9, column=0, sticky="w", pady=(0, 5))

    dir_label = Label(main_frame, text="No directory selected", bg=system_bg, fg=text_color)
    dir_label.grid(row=10, column=0, sticky="w", pady=(0, 10))

    # bottom Buttons
    def open_github():
        """Open the GitHub repository link in the web browser."""
        webbrowser.open("https://github.com/PaschalisAg/WikiTextGraph")

    def contact_developer():
        """Open an email client to contact the developer."""
        webbrowser.open("mailto:pasxalisag9@gmail.com?subject=WikiTextGraph%20Support")

    confirm_button = Button(root, text="Start Processing", font=("Arial", 12, "bold"), bg=button_color_start, fg=button_text_color, width=20, command=on_start)
    confirm_button.grid(row=11, column=0, pady=10, sticky="ew")

    lower_buttons_frame = Frame(root, bg=system_bg)
    lower_buttons_frame.grid(row=12, column=0, pady=10)

    github_button = Button(lower_buttons_frame, text="GitHub Repo", font=("Arial", 12), bg=button_color_github, fg=button_text_color, width=15, command=open_github)
    github_button.grid(row=0, column=0, padx=20)

    contact_button = Button(lower_buttons_frame, text="Contact Dev", font=("Arial", 12), bg=button_color_contact, fg=button_text_color, width=15, command=contact_developer)
    contact_button.grid(row=0, column=1, padx=20)

    root.mainloop()
    
    # return the values so that the algorithm can start running
    return dump_filepath, selected_language.get(), base_dir, generate_graph_flag.get()# , use_string_labels.get()
