import tkinter as tk
import tkinter.ttk as ttk

from lang import ZHCN as lang


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(lang.title)
        self.main_notebook = ttk.Notebook(self)
        midi_page = ttk.Frame(self.main_notebook)
        self.main_notebook.add(midi_page, text=lang.midi_tab)

        midi_path_label = ttk.Label(midi_page, text="MIDI file path:")
        self.midi_path = ttk.Entry(midi_page)
        browse_midi_path = ttk.Button(midi_page, text=lang.browse, command=None)
        midi_path_label.grid(row=0, column=0, padx=5, pady=5)
        self.midi_path.grid(row=0, column=1, padx=5, pady=5)
        browse_midi_path.grid(row=0, column=2, padx=5, pady=5)

        world_path_label = ttk.Label(midi_page, text="World name:")
        self.world_path = ttk.Entry(midi_page)
        world_path_label.grid(row=2, column=0, padx=5, pady=5)
        self.world_path.grid(row=2, column=1, padx=5, pady=5, columnspan=2)

        self.pan_enable = ttk.Checkbutton(midi_page, text="Enable Pan")
        self.drum_enable = ttk.Checkbutton(midi_page, text="Enable N-Track-10 Drum")
        self.pitch_enable = ttk.Checkbutton(midi_page, text="Enable Pitch")
        self.gvol_enable = ttk.Checkbutton(midi_page, text="Enable Global Volume")
        self.pan_enable.grid(row=3, column=0, padx=5, pady=5)
        self.drum_enable.grid(row=3, column=1, padx=5, pady=5, columnspan=2)
        self.pitch_enable.grid(row=4, column=0, padx=5, pady=5)
        self.gvol_enable.grid(row=4, column=1, padx=5, pady=5, columnspan=2)

        pitch_factor_label = ttk.Label(midi_page, text="Pitch Factor:")
        self.pitch_factor_value = ttk.Spinbox(midi_page)
        pitch_factor_label.grid(row=5, column=0, padx=5, pady=5)
        self.pitch_factor_value.grid(row=5, column=1, padx=5, pady=5, columnspan=2)

        volume_factor_label = ttk.Label(midi_page, text="Volume Factor:")
        self.volume_factor_value = ttk.Spinbox(midi_page)
        volume_factor_label.grid(row=6, column=0, padx=5, pady=5)
        self.volume_factor_value.grid(row=6, column=1, padx=5, pady=5, columnspan=2)

        generate_button = ttk.Button(midi_page, text="GENERATE NOW!!", command=self.midi_call)
        generate_button.grid(row=7, column=0, padx=5, pady=5, columnspan=3)

        pic_page = ttk.Frame(self.main_notebook)
        self.main_notebook.add(pic_page, text=lang.picture_tab)

        video_page = ttk.Frame(self.main_notebook)
        self.main_notebook.add(video_page, text=lang.video_tab)

        config_page = ttk.Frame(self.main_notebook)
        self.main_notebook.add(config_page, text=lang.config_tab)

        mc_path_label = ttk.Label(config_page, text=lang.dot_mc_path)
        self.mc_path = ttk.Entry(config_page)
        browse_mc_path = ttk.Button(config_page, text=lang.browse)
        mc_path_label.grid(row=1, column=0, padx=5, pady=5)
        self.mc_path.grid(row=1, column=1, padx=5, pady=5)
        browse_mc_path.grid(row=1, column=2, padx=5, pady=5)

        mc_ver_label = ttk.Label(config_page, text=lang.version_name)
        self.mc_ver = ttk.Combobox(config_page)
        mc_ver_label.grid(row=2, column=0, padx=5, pady=5)
        self.mc_ver.grid(row=2, column=1, padx=5, pady=5, columnspan=2)

        mc_world_label = ttk.Label(config_page, text=lang.world_name)
        self.mc_world = ttk.Combobox(config_page)
        mc_world_label.grid(row=3, column=0, padx=5, pady=5)
        self.mc_world.grid(row=3, column=1, padx=5, pady=5, columnspan=2)

        pack_name_label = ttk.Label(config_page, text=lang.package_name)

        self.pack_name = ttk.Entry(config_page)
        default_pack_name = ttk.Button(config_page, text=lang.default)
        pack_name_label.grid(row=4, column=0, padx=5, pady=5)
        self.pack_name.grid(row=4, column=1, padx=5, pady=5)
        default_pack_name.grid(row=4, column=2, padx=5, pady=5)

        about_page = ttk.Frame(self.main_notebook)
        self.main_notebook.add(about_page, text=lang.about_tab)
        tk.Label(about_page, text=lang.about_project, font=("simhei", 24, "bold")).pack()
        tk.Label(about_page, text=lang.about_author, font=("simsun", 10, "italic")).pack()
        tk.Label(about_page, text=lang.about_text, font=("simhei", 12)).pack()

        self.main_notebook.pack(padx=10, pady=10, fill="both", expand=True)

        copy = tk.Label(self, text="Copyright (c) 2020 kworker (Frank Yang). Under GPL license.")
        copy.pack(fill="x", side="bottom")

    def midi_call(self):
        pass


if __name__ == '__main__':
    app = Application()
    app.mainloop()
