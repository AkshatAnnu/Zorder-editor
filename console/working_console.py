#!/usr/bin/env python3
"""
Working Zorder Console - Fixed version
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WorkingConsole:
    def __init__(self, root):
        self.root = root
        self.root.title("Zorder Bill Editor Console")
        self.root.geometry("500x400")
        
        # Configuration
        self.server_url = os.getenv("SERVER_URL", "http://127.0.0.1:8000")
        
        self.create_ui()
    
    def create_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_frame, text="Zorder Bill Editor Console", 
                              font=("Arial", 16, "bold"), bg="white")
        title_label.pack(pady=(0, 20))
        
        # Server Configuration Frame
        server_frame = tk.LabelFrame(main_frame, text="Server Configuration", 
                                   font=("Arial", 12, "bold"), bg="white")
        server_frame.pack(fill=tk.X, pady=(0, 20))
        
        server_inner = tk.Frame(server_frame, bg="white")
        server_inner.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(server_inner, text="Server URL:", bg="white").pack(anchor=tk.W)
        self.server_var = tk.StringVar(value=self.server_url)
        server_entry = tk.Entry(server_inner, textvariable=self.server_var, width=50)
        server_entry.pack(fill=tk.X, pady=(5, 10))
        
        test_btn = tk.Button(server_inner, text="Test Connection", 
                           command=self.test_connection, bg="blue", fg="white")
        test_btn.pack(anchor=tk.W)
        
        # Form Frame
        form_frame = tk.LabelFrame(main_frame, text="Bill Edit Request", 
                                 font=("Arial", 12, "bold"), bg="white")
        form_frame.pack(fill=tk.X, pady=(0, 20))
        
        form_inner = tk.Frame(form_frame, bg="white")
        form_inner.pack(fill=tk.X, padx=10, pady=10)
        
        # Invoice ID
        tk.Label(form_inner, text="Invoice ID:", bg="white").pack(anchor=tk.W)
        self.invoice_id_var = tk.StringVar()
        invoice_entry = tk.Entry(form_inner, textvariable=self.invoice_id_var, width=40)
        invoice_entry.pack(fill=tk.X, pady=(5, 10))
        
        # Biller ID
        tk.Label(form_inner, text="Biller ID:", bg="white").pack(anchor=tk.W)
        self.biller_id_var = tk.StringVar()
        biller_entry = tk.Entry(form_inner, textvariable=self.biller_id_var, width=40)
        biller_entry.pack(fill=tk.X, pady=(5, 10))
        
        # Machine ID
        tk.Label(form_inner, text="Machine ID:", bg="white").pack(anchor=tk.W)
        self.machine_id_var = tk.StringVar()
        machine_entry = tk.Entry(form_inner, textvariable=self.machine_id_var, width=40)
        machine_entry.pack(fill=tk.X, pady=(5, 10))
        
        # Admin URL
        tk.Label(form_inner, text="Admin URL (optional):", bg="white").pack(anchor=tk.W)
        self.admin_url_var = tk.StringVar()
        admin_entry = tk.Entry(form_inner, textvariable=self.admin_url_var, width=40)
        admin_entry.pack(fill=tk.X, pady=(5, 10))
        
        # Buttons
        btn_frame = tk.Frame(main_frame, bg="white")
        btn_frame.pack(fill=tk.X, pady=20)
        
        send_btn = tk.Button(btn_frame, text="Send WhatsApp YES/NO", 
                           command=self.send_approval_request, bg="green", fg="white",
                           font=("Arial", 12, "bold"))
        send_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_btn = tk.Button(btn_frame, text="Clear", command=self.clear_form)
        clear_btn.pack(side=tk.LEFT)
        
        # Status Frame
        status_frame = tk.LabelFrame(main_frame, text="Status", 
                                   font=("Arial", 12, "bold"), bg="white")
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        status_inner = tk.Frame(status_frame, bg="white")
        status_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status text
        self.status_text = tk.Text(status_inner, height=6, wrap=tk.WORD, 
                                  font=("Courier", 10))
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(status_inner, orient=tk.VERTICAL, 
                               command=self.status_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        # Initial status
        self.add_status_message("Ready to send approval requests...")
    
    def add_status_message(self, message):
        """Add a message to the status text area."""
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
    
    def test_connection(self):
        """Test connection to the server."""
        try:
            server_url = self.server_var.get().strip()
            if not server_url:
                messagebox.showerror("Error", "Please enter server URL")
                return
            
            self.add_status_message(f"Testing connection to {server_url}...")
            
            response = requests.get(f"{server_url}/healthz", timeout=10)
            response.raise_for_status()
            
            self.add_status_message("✅ Connection successful!")
            messagebox.showinfo("Success", "Connection to server successful!")
            
        except requests.exceptions.RequestException as e:
            error_msg = f"❌ Connection failed: {str(e)}"
            self.add_status_message(error_msg)
            messagebox.showerror("Connection Failed", f"Failed to connect to server:\n{str(e)}")
        except Exception as e:
            error_msg = f"❌ Unexpected error: {str(e)}"
            self.add_status_message(error_msg)
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")
    
    def validate_form(self):
        """Validate form inputs."""
        if not self.invoice_id_var.get().strip():
            messagebox.showerror("Validation Error", "Invoice ID is required")
            return False
        
        if not self.biller_id_var.get().strip():
            messagebox.showerror("Validation Error", "Biller ID is required")
            return False
        
        if not self.machine_id_var.get().strip():
            messagebox.showerror("Validation Error", "Machine ID is required")
            return False
        
        server_url = self.server_var.get().strip()
        if not server_url:
            messagebox.showerror("Validation Error", "Server URL is required")
            return False
        
        return True
    
    def send_approval_request(self):
        """Send approval request to the server."""
        if not self.validate_form():
            return
        
        try:
            # Prepare request data
            data = {
                "invoice_id": self.invoice_id_var.get().strip(),
                "biller_id": self.biller_id_var.get().strip(),
                "machine_id": self.machine_id_var.get().strip(),
            }
            
            admin_url = self.admin_url_var.get().strip()
            if admin_url:
                data["admin_url"] = admin_url
            
            server_url = self.server_var.get().strip()
            
            self.add_status_message(f"Sending approval request...")
            self.add_status_message(f"Data: {json.dumps(data, indent=2)}")
            
            # Send request
            response = requests.post(
                f"{server_url}/event/bill-edited",
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                action_id = result.get("action_id", "unknown")
                
                success_msg = f"✅ Approval request sent successfully!\nAction ID: {action_id}"
                self.add_status_message(success_msg)
                messagebox.showinfo("Success", "WhatsApp approval request sent successfully!\n\n"
                                              f"Action ID: {action_id}\n\n"
                                              "The owner will receive YES/NO buttons on WhatsApp.")
                
                # Clear form after successful send
                self.clear_form()
                
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_msg = error_data.get("error", f"HTTP {response.status_code}")
                details = error_data.get("details", "")
                
                full_error = f"❌ Request failed: {error_msg}"
                if details:
                    full_error += f"\nDetails: {details}"
                
                self.add_status_message(full_error)
                messagebox.showerror("Request Failed", full_error)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"❌ Network error: {str(e)}"
            self.add_status_message(error_msg)
            messagebox.showerror("Network Error", f"Failed to send request:\n{str(e)}")
            
        except Exception as e:
            error_msg = f"❌ Unexpected error: {str(e)}"
            self.add_status_message(error_msg)
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")
    
    def clear_form(self):
        """Clear all form inputs."""
        self.invoice_id_var.set("")
        self.biller_id_var.set("")
        self.machine_id_var.set("")
        self.admin_url_var.set("")

def main():
    """Main function to run the console application."""
    root = tk.Tk()
    app = WorkingConsole(root)
    root.mainloop()

if __name__ == "__main__":
    main()
