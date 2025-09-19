#!/usr/bin/env python3
"""
Ultra Simple Tkinter Test
"""
import tkinter as tk

print("Starting basic tkinter test...")

root = tk.Tk()
root.title("Basic Test")
root.geometry("300x200")

print("Creating label...")
label = tk.Label(root, text="Hello World!", font=("Arial", 14))
label.pack(pady=50)

print("Creating button...")
button = tk.Button(root, text="Click Me", command=lambda: print("Button clicked!"))
button.pack()

print("Starting mainloop...")
root.mainloop()
print("Window closed")
