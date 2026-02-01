# main.py
import customtkinter as ctk
from ui.app import PsychoTestApp

if __name__ == "__main__":
    # * Устанавливаем светлую тему и синюю цветовую схему - как в большинстве образовательных приложений
    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")

    app = PsychoTestApp()
    app.mainloop()