#!/usr/bin/env python3
"""
Simple Debug Console - Test version
"""
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json

class SimpleConsole:
    def __init__(self, root):
        self.root = root
        self.root.title("Zorder Debug Console")
        self.root.geometry("400x300")
        
        # Create simple UI
        self.create_ui()
    
    def create_ui(self):
        # Simple label
        label = tk.Label(self.root, text="Zorder Bill Editor Console", 
                        font=("Arial", 16, "bold"))
        label.pack(pady=20)
        
        # Server URL
        tk.Label(self.root, text="Server URL:").pack()
        self.server_entry = tk.Entry(self.root, width=50)
        self.server_entry.pack(pady=5)
        self.server_entry.insert(0, "http://127.0.0.1:8000")
        
        # Invoice ID
        tk.Label(self.root, text="Invoice ID:").pack(pady=(10,0))
        self.invoice_entry = tk.Entry(self.root, width=30)
        self.invoice_entry.pack(pady=5)
        
        # Biller ID
        tk.Label(self.root, text="Biller ID:").pack()
        self.biller_entry = tk.Entry(self.root, width=30)
        self.biller_entry.pack(pady=5)
        
        # Machine ID
        tk.Label(self.root, text="Machine ID:").pack()
        self.machine_entry = tk.Entry(self.root, width=30)
        self.machine_entry.pack(pady=5)
        
        # Button
        button = tk.Button(self.root, text="Send Request", 
                          command=self.send_request, bg="green", fg="white")
        button.pack(pady=20)
        
        # Status
        self.status_label = tk.Label(self.root, text="Ready...", fg="blue")
        self.status_label.pack()
    
    def send_request(self):
        try:
            data = {
                "invoice_id": self.invoice_entry.get(),
                "biller_id": self.biller_entry.get(),
                "machine_id": self.machine_entry.get()
            }
            
            server_url = self.server_entry.get()
            self.status_label.config(text="Sending request...", fg="orange")
            
            response = requests.post(f"{server_url}/event/bill-edited", 
                                   json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                action_id = result.get("action_id", "unknown")
                self.status_label.config(text=f"Success! Action ID: {action_id}", fg="green")
                messagebox.showinfo("Success", f"Request sent! Action ID: {action_id}")
            else:
                self.status_label.config(text="Request failed!", fg="red")
                messagebox.showerror("Error", f"Request failed: {response.status_code}")
                
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")
            messagebox.showerror("Error", f"Error: {str(e)}")

def main():
    root = tk.Tk()
    app = SimpleConsole(root)
    root.mainloop()

if __name__ == "__main__":
    main()
