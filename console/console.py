#!/usr/bin/env python3
"""
Zorder Console - Owner GUI for sending WhatsApp approval requests
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ZorderConsole:
    def __init__(self, root):
        self.root = root
        self.root.title("Zorder Bill Editor Console")
        self.root.geometry("500x400")
        self.root.resizable(True, True)
        
        # Configuration
        self.server_url = os.getenv("SERVER_URL", "http://127.0.0.1:8000")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the main user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Zorder Bill Editor Console", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Server URL display
        server_frame = ttk.LabelFrame(main_frame, text="Server Configuration", padding="10")
        server_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        server_frame.columnconfigure(1, weight=1)
        
        ttk.Label(server_frame, text="Server URL:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.server_var = tk.StringVar(value=self.server_url)
        server_entry = ttk.Entry(server_frame, textvariable=self.server_var, width=50)
        server_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Test connection button
        test_btn = ttk.Button(server_frame, text="Test Connection", command=self.test_connection)
        test_btn.grid(row=0, column=2, padx=(10, 0))
        
        # Input form
        form_frame = ttk.LabelFrame(main_frame, text="Bill Edit Request", padding="10")
        form_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        form_frame.columnconfigure(1, weight=1)
        
        # Invoice ID
        ttk.Label(form_frame, text="Invoice ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.invoice_id_var = tk.StringVar()
        invoice_entry = ttk.Entry(form_frame, textvariable=self.invoice_id_var)
        invoice_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Biller ID
        ttk.Label(form_frame, text="Biller ID:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.biller_id_var = tk.StringVar()
        biller_entry = ttk.Entry(form_frame, textvariable=self.biller_id_var)
        biller_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Machine ID
        ttk.Label(form_frame, text="Machine ID:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.machine_id_var = tk.StringVar()
        machine_entry = ttk.Entry(form_frame, textvariable=self.machine_id_var)
        machine_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Admin URL (optional)
        ttk.Label(form_frame, text="Admin URL (optional):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.admin_url_var = tk.StringVar()
        admin_entry = ttk.Entry(form_frame, textvariable=self.admin_url_var)
        admin_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        # Send button
        send_btn = ttk.Button(btn_frame, text="Send WhatsApp YES/NO", 
                             command=self.send_approval_request)
        send_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear button
        clear_btn = ttk.Button(btn_frame, text="Clear", command=self.clear_form)
        clear_btn.pack(side=tk.LEFT)
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(0, weight=1)
        
        # Status text
        self.status_text = tk.Text(status_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Scrollbar for status text
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        # Set focus to first input
        invoice_entry.focus()
        
        # Initial status message
        self.add_status_message("Ready to send approval requests...")
    
    def add_status_message(self, message):
        """Add a message to the status text area."""
        self.status_text.configure(state=tk.NORMAL)
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.configure(state=tk.DISABLED)
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
    app = ZorderConsole(root)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()
