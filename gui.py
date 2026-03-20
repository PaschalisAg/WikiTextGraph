import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from pathlib import Path
import webbrowser


# ── Colorblind-safe palette (Wong 2011 / IBM palette) 
# Avoids red/green confusion. Works for deuteranopia, protanopia, tritanopia.
PALETTE = {
    "bg":           "#F7F8FA",   # near-white surface
    "card":         "#FFFFFF",   # card/panel background
    "border":       "#DDE1E7",   # subtle borders
    "accent":       "#0072B2",   # IBM blue  – primary action / headings
    "accent_hover": "#005A8E",   # darker blue for hover
    "cta":          "#E69F00",   # amber – call-to-action button (≠ red/green)
    "cta_hover":    "#C17F00",
    "text":         "#1C1C2E",   # near-black body text
    "muted":        "#6B7280",   # secondary / placeholder text
    "success":      "#009E73",   # teal – colorblind-safe "selected" indicator
    "divider":      "#E5E7EB",
}

FONT_HEADING  = ("Georgia", 18, "bold")
FONT_SUBHEAD  = ("Georgia", 11, "italic")
FONT_STEP     = ("Courier", 11, "bold")
FONT_BODY     = ("Helvetica Neue", 10)
FONT_BODY_B   = ("Helvetica Neue", 10, "bold")
FONT_SMALL    = ("Helvetica Neue", 9)
FONT_BTN      = ("Helvetica Neue", 10, "bold")
FONT_CTA      = ("Helvetica Neue", 12, "bold")


def _badge(parent, number, bg):
    """Circular step-number badge drawn on a Canvas."""
    size = 26
    c = tk.Canvas(parent, width=size, height=size, bg=bg,
                  highlightthickness=0)
    c.create_oval(1, 1, size - 1, size - 1, fill=PALETTE["accent"], outline="")
    c.create_text(size // 2, size // 2, text=str(number),
                  fill="white", font=("Helvetica Neue", 10, "bold"))
    return c


def _card(parent, **kw):
    """Raised card frame with a hairline border."""
    f = tk.Frame(parent, bg=PALETTE["card"],
                 highlightbackground=PALETTE["border"],
                 highlightthickness=1, **kw)
    return f


def _divider(parent):
    return tk.Frame(parent, height=1, bg=PALETTE["divider"])


def _browse_btn(parent, text, command):
    """Flat 'Browse…' button with hover feedback."""
    btn = tk.Button(
        parent, text=text, command=command,
        bg=PALETTE["accent"], fg="white",
        activebackground=PALETTE["accent_hover"], activeforeground="white",
        font=FONT_BTN, relief="flat", cursor="hand2",
        padx=14, pady=6, bd=0,
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=PALETTE["accent_hover"]))
    btn.bind("<Leave>", lambda e: btn.config(bg=PALETTE["accent"]))
    return btn


def _status_label(parent):
    """Label that shows a selected path / 'Nothing selected yet'."""
    lbl = tk.Label(parent, text="Nothing selected yet",
                   font=FONT_SMALL, bg=PALETTE["card"],
                   fg=PALETTE["muted"], anchor="w", wraplength=380)
    return lbl


def gui_prompt_for_inputs():
    """
    Launches a Tkinter-based GUI to prompt for user inputs:
      1) Wikipedia dump file path,
      2) Language code,
      3) Whether to generate a graph,
      4) Output directory.

    Returns:
        (dump_filepath, selected_language, base_dir, generate_graph_flag)
    """

    root = tk.Tk()
    root.title("WikiTextGraph")
    root.geometry("560x780")
    root.resizable(False, False)
    root.configure(bg=PALETTE["bg"])
    root.columnconfigure(0, weight=1)

    # ── mutable state 
    dump_filepath   = None
    base_dir        = None
    selected_language   = tk.StringVar(root)
    generate_graph_flag = tk.BooleanVar(value=True)

    # ── helpers 
    def _mark_selected(label, path_name):
        label.config(text=f"✔  {path_name}",
                     fg=PALETTE["success"], font=FONT_SMALL)

    # ── HEADER 
    header = tk.Frame(root, bg=PALETTE["accent"], pady=18)
    header.grid(row=0, column=0, sticky="ew")
    header.columnconfigure(0, weight=1)

    tk.Label(header, text="WikiTextGraph",
             font=FONT_HEADING, bg=PALETTE["accent"], fg="white"
             ).grid(row=0, column=0)
    tk.Label(header, text="Wikipedia XML Dump Processing Tool",
             font=FONT_SUBHEAD, bg=PALETTE["accent"], fg="#BDD7F0"
             ).grid(row=1, column=0, pady=(2, 0))

    # ── LOGO / FUNDING 
    try:
        logo_path = "logo/mestizajes_logo-removebg-preview.png"
        if os.path.exists(logo_path):
            logo_img = tk.PhotoImage(file=logo_path).subsample(4, 4)
            logo_row = tk.Frame(root, bg=PALETTE["bg"], pady=8)
            logo_row.grid(row=1, column=0)
            lbl = tk.Label(logo_row, image=logo_img, bg=PALETTE["bg"])
            lbl.image = logo_img
            lbl.pack(side="left", padx=(0, 8))
            tk.Label(logo_row, text="Funded by Mestizajes",
                     font=("Helvetica Neue", 9, "italic"),
                     bg=PALETTE["bg"], fg=PALETTE["muted"]).pack(side="left")
    except Exception as e:
        print(f"Logo load error: {e}")

    # ── SCROLL CANVAS (main content) 
    content = tk.Frame(root, bg=PALETTE["bg"])
    content.grid(row=2, column=0, padx=28, pady=(8, 0), sticky="nsew")
    content.columnconfigure(0, weight=1)

    # ── STEP 1 
    card1 = _card(content)
    card1.grid(row=0, column=0, sticky="ew", pady=(0, 12))
    card1.columnconfigure(1, weight=1)

    badge1 = _badge(card1, 1, PALETTE["card"])
    badge1.grid(row=0, column=0, padx=(14, 10), pady=14, sticky="n")

    step1_inner = tk.Frame(card1, bg=PALETTE["card"])
    step1_inner.grid(row=0, column=1, sticky="ew", padx=(0, 14), pady=12)
    step1_inner.columnconfigure(0, weight=1)

    tk.Label(step1_inner, text="Select Compressed XML Dump File",
             font=FONT_BODY_B, bg=PALETTE["card"], fg=PALETTE["text"],
             anchor="w").grid(row=0, column=0, sticky="w")
    tk.Label(step1_inner, text="Accepts .bz2 Wikipedia dump archives",
             font=FONT_SMALL, bg=PALETTE["card"], fg=PALETTE["muted"],
             anchor="w").grid(row=1, column=0, sticky="w", pady=(1, 8))

    dump_status = _status_label(step1_inner)
    dump_status.grid(row=3, column=0, sticky="w", pady=(6, 0))

    def select_dump_file():
        nonlocal dump_filepath
        f = filedialog.askopenfilename(
            title="Select the compressed XML dump file",
            filetypes=[("BZ2 files", "*.bz2"), ("All files", "*.*")])
        if f:
            dump_filepath = Path(f)
            _mark_selected(dump_status, dump_filepath.name)

    _browse_btn(step1_inner, "Browse…", select_dump_file
                ).grid(row=2, column=0, sticky="w")

    # ── STEP 2 
    card2 = _card(content)
    card2.grid(row=1, column=0, sticky="ew", pady=(0, 12))
    card2.columnconfigure(1, weight=1)

    badge2 = _badge(card2, 2, PALETTE["card"])
    badge2.grid(row=0, column=0, padx=(14, 10), pady=14, sticky="n")

    step2_inner = tk.Frame(card2, bg=PALETTE["card"])
    step2_inner.grid(row=0, column=1, sticky="ew", padx=(0, 14), pady=12)

    tk.Label(step2_inner, text="Select Language",
             font=FONT_BODY_B, bg=PALETTE["card"], fg=PALETTE["text"],
             anchor="w").grid(row=0, column=0, sticky="w")
    tk.Label(step2_inner, text="Language code of the Wikipedia dump",
             font=FONT_SMALL, bg=PALETTE["card"], fg=PALETTE["muted"],
             anchor="w").grid(row=1, column=0, sticky="w", pady=(1, 8))

    available_languages = sorted(["en", "es", "el", "pl", "it",
                                   "nl", "eu", "hi", "de", "vi", "uk"])
    selected_language.set(available_languages[0])

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Modern.TCombobox",
                    fieldbackground=PALETTE["card"],
                    background=PALETTE["card"],
                    foreground=PALETTE["text"],
                    arrowcolor=PALETTE["accent"],
                    bordercolor=PALETTE["border"],
                    lightcolor=PALETTE["card"],
                    darkcolor=PALETTE["card"],
                    selectbackground=PALETTE["accent"],
                    selectforeground="white")

    combo = ttk.Combobox(step2_inner, textvariable=selected_language,
                         values=available_languages, state="readonly",
                         width=10, style="Modern.TCombobox")
    combo.grid(row=2, column=0, sticky="w")

    # ── STEP 3 
    card3 = _card(content)
    card3.grid(row=2, column=0, sticky="ew", pady=(0, 12))
    card3.columnconfigure(1, weight=1)

    badge3 = _badge(card3, 3, PALETTE["card"])
    badge3.grid(row=0, column=0, padx=(14, 10), pady=14, sticky="n")

    step3_inner = tk.Frame(card3, bg=PALETTE["card"])
    step3_inner.grid(row=0, column=1, sticky="ew", padx=(0, 14), pady=12)

    tk.Label(step3_inner, text="Generate Graph?",
             font=FONT_BODY_B, bg=PALETTE["card"], fg=PALETTE["text"],
             anchor="w").grid(row=0, column=0, columnspan=2, sticky="w")
    tk.Label(step3_inner, text="Produce a co-occurrence graph from the parsed text",
             font=FONT_SMALL, bg=PALETTE["card"], fg=PALETTE["muted"],
             anchor="w").grid(row=1, column=0, columnspan=2, sticky="w", pady=(1, 8))

    radio_kw = dict(variable=generate_graph_flag,
                    bg=PALETTE["card"], fg=PALETTE["text"],
                    activebackground=PALETTE["card"],
                    selectcolor=PALETTE["accent"],   # colorblind-safe fill
                    font=FONT_BODY, cursor="hand2", relief="flat")

    tk.Radiobutton(step3_inner, text="Yes — generate graph",
                   value=True, **radio_kw
                   ).grid(row=2, column=0, sticky="w", padx=(0, 20))
    tk.Radiobutton(step3_inner, text="No — skip graph generation",
                   value=False, **radio_kw
                   ).grid(row=2, column=1, sticky="w")

    # ── STEP 4 
    card4 = _card(content)
    card4.grid(row=3, column=0, sticky="ew", pady=(0, 12))
    card4.columnconfigure(1, weight=1)

    badge4 = _badge(card4, 4, PALETTE["card"])
    badge4.grid(row=0, column=0, padx=(14, 10), pady=14, sticky="n")

    step4_inner = tk.Frame(card4, bg=PALETTE["card"])
    step4_inner.grid(row=0, column=1, sticky="ew", padx=(0, 14), pady=12)
    step4_inner.columnconfigure(0, weight=1)

    tk.Label(step4_inner, text="Select Output Directory",
             font=FONT_BODY_B, bg=PALETTE["card"], fg=PALETTE["text"],
             anchor="w").grid(row=0, column=0, sticky="w")
    tk.Label(step4_inner, text="Processed files will be saved here",
             font=FONT_SMALL, bg=PALETTE["card"], fg=PALETTE["muted"],
             anchor="w").grid(row=1, column=0, sticky="w", pady=(1, 8))

    dir_status = _status_label(step4_inner)
    dir_status.grid(row=3, column=0, sticky="w", pady=(6, 0))

    def select_output_dir():
        nonlocal base_dir
        d = filedialog.askdirectory(title="Select the output directory")
        if d:
            base_dir = Path(d)
            _mark_selected(dir_status, str(base_dir))

    _browse_btn(step4_inner, "Browse…", select_output_dir
                ).grid(row=2, column=0, sticky="w")

    # ── FOOTER BUTTONS ─────────────────────────────────────────────────────────
    _divider(root).grid(row=3, column=0, sticky="ew", padx=0)

    def on_start():
        nonlocal dump_filepath, base_dir
        if not dump_filepath or not base_dir:
            messagebox.showwarning(
                "Missing Input",
                "Please select both a dump file and an output directory before proceeding.")
            return
        root.quit()
        root.destroy()

    cta = tk.Button(
        root, text="▶  Start Processing", command=on_start,
        bg=PALETTE["cta"], fg="white",
        activebackground=PALETTE["cta_hover"], activeforeground="white",
        font=FONT_CTA, relief="flat", cursor="hand2",
        padx=24, pady=10, bd=0,
    )
    cta.grid(row=4, column=0, padx=28, pady=(14, 8), sticky="ew")
    cta.bind("<Enter>", lambda e: cta.config(bg=PALETTE["cta_hover"]))
    cta.bind("<Leave>", lambda e: cta.config(bg=PALETTE["cta"]))

    link_frame = tk.Frame(root, bg=PALETTE["bg"])
    link_frame.grid(row=5, column=0, pady=(0, 18))

    def _link_btn(parent, text, command):
        b = tk.Button(parent, text=text, command=command,
                      bg=PALETTE["bg"], fg=PALETTE["accent"],
                      activebackground=PALETTE["bg"],
                      activeforeground=PALETTE["accent_hover"],
                      font=("Helvetica Neue", 10, "underline"),
                      relief="flat", cursor="hand2", bd=0)
        b.bind("<Enter>", lambda e: b.config(fg=PALETTE["accent_hover"]))
        b.bind("<Leave>", lambda e: b.config(fg=PALETTE["accent"]))
        return b

    _link_btn(link_frame, "⌥  GitHub Repository",
              lambda: webbrowser.open("https://github.com/PaschalisAg/WikiTextGraph")
              ).grid(row=0, column=0, padx=24)

    _link_btn(link_frame, "✉  Contact Developer",
              lambda: webbrowser.open("mailto:pasxalisag9@gmail.com?subject=WikiTextGraph%20Support")
              ).grid(row=0, column=1, padx=24)

    root.mainloop()

    return dump_filepath, selected_language.get(), base_dir, generate_graph_flag.get()