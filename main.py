# main.py
import customtkinter as ctk
from ui.app import PsychoTestApp

if __name__ == "__main__":
    ctk.set_appearance_mode("Light")
    app = PsychoTestApp()
    app.state('zoomed')  
    app.mainloop()