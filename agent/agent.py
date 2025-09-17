#!/usr/bin/env python3
"""
Zorder Agent - Windows desktop agent for secure autofill and screen recording
"""
import os
import sys
import time
import json
import logging
import threading
import subprocess
import socket
import platform
import uuid
import hmac
import hashlib
from datetime import datetime
from pathlib import Path

import requests
import pyautogui
from pynput import keyboard
from pynput.keyboard import Key, Listener
from dotenv import load_dotenv

from secret_store import load_credentials

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zorder_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ZorderAgent:
    """Main agent class for handling autofill and screen recording."""
    
    def __init__(self):
        # Configuration from environment
        self.server_url = os.getenv("SERVER_URL", "http://127.0.0.1:8000")
        self.machine_id = os.getenv("MACHINE_ID", f"AGENT-{socket.gethostname()}")
        self.record_dir = os.getenv("RECORD_DIR", r"C:\Recordings")
        self.record_seconds = int(os.getenv("RECORD_SECONDS", "180"))
        self.poll_interval = int(os.getenv("POLL_INTERVAL", "5"))
        self.arm_duration = int(os.getenv("ARM_DURATION", "600"))  # 10 minutes
        self.hmac_secret = os.getenv("HMAC_SECRET")
        
        # State variables
        self.is_armed = False
        self.armed_task = None
        self.arm_time = None
        self.recording_process = None
        self.recording_file = None
        self.is_recording = False
        self.credentials = None
        
        # HTTP session for server communication
        self.session = requests.Session()
        if self.hmac_secret:
            self.session.headers.update({
                'X-Machine-ID': self.machine_id,
                'User-Agent': f'ZorderAgent/{self.machine_id}'
            })
        
        # Ensure recording directory exists
        os.makedirs(self.record_dir, exist_ok=True)
        
        # Load credentials
        self.load_user_credentials()
        
        # Setup keyboard listener
        self.keyboard_listener = None
        self.setup_hotkeys()
        
        logger.info(f"Zorder Agent initialized - Machine ID: {self.machine_id}")
    
    def load_user_credentials(self):
        """Load encrypted user credentials."""
        try:
            username, password = load_credentials()
            if username and password:
                self.credentials = {"username": username, "password": password}
                logger.info("User credentials loaded successfully")
            else:
                logger.warning("No credentials found - F5/F6 will not work until credentials are set")
                self.credentials = None
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            self.credentials = None
    
    def setup_hotkeys(self):
        """Setup global hotkey listener."""
        try:
            self.keyboard_listener = Listener(on_press=self.on_key_press)
            self.keyboard_listener.start()
            logger.info("Hotkey listener started (F5=username, F6=password+enter+record, F7=stop)")
        except Exception as e:
            logger.error(f"Failed to setup hotkeys: {e}")
    
    def on_key_press(self, key):
        """Handle global hotkey presses."""
        try:
            if key == Key.f5:
                self.handle_f5()
            elif key == Key.f6:
                self.handle_f6()
            elif key == Key.f7:
                self.handle_f7()
        except Exception as e:
            logger.error(f"Hotkey handler error: {e}")
    
    def handle_f5(self):
        """F5: Type username (only when armed)."""
        if not self.is_armed:
            logger.info("F5 pressed but agent not armed")
            return
        
        if not self.credentials:
            logger.warning("F5 pressed but no credentials available")
            return
        
        try:
            logger.info("F5 pressed - typing username")
            # Small delay to ensure focus
            time.sleep(0.1)
            
            # Type username with small intervals between characters
            pyautogui.typewrite(self.credentials["username"], interval=0.05)
            logger.info("Username typed successfully")
            
        except Exception as e:
            logger.error(f"Failed to type username: {e}")
    
    def handle_f6(self):
        """F6: Type password, press Enter, and start recording (only when armed)."""
        if not self.is_armed:
            logger.info("F6 pressed but agent not armed")
            return
        
        if not self.credentials:
            logger.warning("F6 pressed but no credentials available")
            return
        
        if self.is_recording:
            logger.warning("F6 pressed but already recording")
            return
        
        try:
            logger.info("F6 pressed - typing password and starting recording")
            
            # Small delay to ensure focus
            time.sleep(0.1)
            
            # Type password with small intervals
            pyautogui.typewrite(self.credentials["password"], interval=0.05)
            
            # Press Enter to submit login
            time.sleep(0.2)
            pyautogui.press('enter')
            
            logger.info("Password typed and Enter pressed")
            
            # Start screen recording immediately
            self.start_recording()
            
        except Exception as e:
            logger.error(f"Failed to handle F6: {e}")
    
    def handle_f7(self):
        """F7: Stop recording early."""
        if not self.is_recording:
            logger.info("F7 pressed but not recording")
            return
        
        try:
            logger.info("F7 pressed - stopping recording early")
            self.stop_recording()
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
    
    def start_recording(self):
        """Start screen recording using ffmpeg."""
        if self.is_recording:
            logger.warning("Recording already in progress")
            return
        
        try:
            # Generate recording filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{self.machine_id}_{timestamp}.mp4"
            self.recording_file = os.path.join(self.record_dir, filename)
            
            # FFmpeg command for Windows desktop recording
            ffmpeg_cmd = [
                'ffmpeg',
                '-f', 'gdigrab',           # Windows desktop capture
                '-framerate', '15',         # 15 FPS for smaller file size
                '-i', 'desktop',           # Capture entire desktop
                '-t', str(self.record_seconds),  # Duration limit
                '-vf', 'scale=1280:720',   # Scale to 720p
                '-c:v', 'libx264',         # H.264 codec
                '-preset', 'ultrafast',    # Fast encoding
                '-crf', '28',              # Compression (higher = smaller file)
                '-pix_fmt', 'yuv420p',     # Pixel format for compatibility
                '-y',                      # Overwrite output file
                self.recording_file
            ]
            
            logger.info(f"Starting recording: {filename}")
            
            # Start ffmpeg process
            self.recording_process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW  # Hide window
            )
            
            self.is_recording = True
            
            # Start timer thread to stop recording automatically
            timer_thread = threading.Thread(target=self.recording_timer)
            timer_thread.daemon = True
            timer_thread.start()
            
            logger.info(f"Recording started successfully - will auto-stop in {self.record_seconds}s")
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.is_recording = False
            self.recording_process = None
            self.recording_file = None
    
    def recording_timer(self):
        """Timer thread to automatically stop recording."""
        try:
            time.sleep(self.record_seconds)
            if self.is_recording:
                logger.info("Recording duration reached - stopping automatically")
                self.stop_recording()
        except Exception as e:
            logger.error(f"Recording timer error: {e}")
    
    def stop_recording(self):
        """Stop screen recording and upload."""
        if not self.is_recording:
            return
        
        try:
            logger.info("Stopping recording...")
            
            # Terminate ffmpeg process
            if self.recording_process:
                self.recording_process.terminate()
                self.recording_process.wait(timeout=10)
                self.recording_process = None
            
            self.is_recording = False
            
            # Wait a moment for file to be fully written
            time.sleep(1)
            
            # Check if recording file exists and has content
            if self.recording_file and os.path.exists(self.recording_file):
                file_size = os.path.getsize(self.recording_file)
                if file_size > 0:
                    logger.info(f"Recording saved: {self.recording_file} ({file_size} bytes)")
                    
                    # Upload recording in background thread
                    upload_thread = threading.Thread(target=self.upload_recording)
                    upload_thread.daemon = True
                    upload_thread.start()
                else:
                    logger.warning(f"Recording file is empty: {self.recording_file}")
            else:
                logger.warning("Recording file not found or not created")
            
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
        finally:
            self.is_recording = False
            self.recording_process = None
    
    def upload_recording(self):
        """Upload recording to server and consume task."""
        try:
            if not self.recording_file or not os.path.exists(self.recording_file):
                logger.error("No recording file to upload")
                return
            
            logger.info(f"Uploading recording: {self.recording_file}")
            
            # Prepare metadata
            meta = {
                "machine_id": self.machine_id,
                "invoice_id": self.armed_task.get("invoice_id", "") if self.armed_task else "",
                "action_id": self.armed_task.get("id", "") if self.armed_task else "",
                "biller_id": self.armed_task.get("biller_id", "") if self.armed_task else "",
                "time": datetime.now().isoformat(),
                "host": socket.gethostname(),
                "ip": self.get_local_ip(),
                "mac": self.get_mac_address(),
                "os": f"{platform.system()} {platform.release()}",
                "duration": self.record_seconds,
                "file_size": os.path.getsize(self.recording_file)
            }
            
            # Prepare files and data for upload
            files = {
                'file': (os.path.basename(self.recording_file), 
                        open(self.recording_file, 'rb'), 
                        'video/mp4')
            }
            
            data = {
                'meta': json.dumps(meta)
            }
            
            # Prepare headers with optional HMAC
            headers = {}
            if self.hmac_secret:
                headers.update(self.get_hmac_headers(json.dumps(meta)))
            
            # Upload to server
            response = requests.post(
                f"{self.server_url}/upload/recording",
                files=files,
                data=data,
                headers=headers,
                timeout=300  # 5 minute timeout for upload
            )
            
            files['file'][1].close()  # Close file handle
            
            if response.status_code == 200:
                logger.info("Recording uploaded successfully")
                
                # Consume the task
                if self.armed_task:
                    self.consume_task(self.armed_task["id"])
                
                # Disarm after successful upload
                self.disarm()
                
            else:
                logger.error(f"Recording upload failed: HTTP {response.status_code}")
                logger.error(f"Response: {response.text}")
            
        except Exception as e:
            logger.error(f"Failed to upload recording: {e}")
        finally:
            # Clean up recording file
            try:
                if self.recording_file and os.path.exists(self.recording_file):
                    os.remove(self.recording_file)
                    logger.info("Recording file cleaned up")
            except Exception as e:
                logger.warning(f"Failed to clean up recording file: {e}")
            
            self.recording_file = None
    
    def get_hmac_headers(self, body):
        """Generate HMAC headers for request authentication."""
        if not self.hmac_secret:
            return {}
        
        signature = hmac.new(
            self.hmac_secret.encode(),
            f"{self.machine_id}{body}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        return {
            "X-Machine-Id": self.machine_id,
            "X-Signature": signature
        }
    
    def get_local_ip(self):
        """Get local IP address."""
        try:
            # Connect to a remote address to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "unknown"
    
    def get_mac_address(self):
        """Get MAC address."""
        try:
            mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
            return ":".join([mac[e:e+2] for e in range(0, 11, 2)])
        except:
            return "unknown"
    
    def poll_tasks(self):
        """Poll server for approved tasks."""
        try:
            response = requests.get(
                f"{self.server_url}/tasks/{self.machine_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                tasks = response.json()
                if tasks and not self.is_armed:
                    # Arm with the first available task
                    self.arm_with_task(tasks[0])
                elif not tasks and self.is_armed:
                    # Check if armed task is still valid
                    self.check_arm_expiry()
            else:
                logger.warning(f"Task polling failed: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to poll tasks: {e}")
    
    def arm_with_task(self, task):
        """Arm the agent with a specific task."""
        self.is_armed = True
        self.armed_task = task
        self.arm_time = time.time()
        
        logger.info(f"Agent ARMED with task {task['id']} for invoice {task['invoice_id']}")
        logger.info(f"Armed for {self.arm_duration} seconds - F5/F6 hotkeys active")
    
    def check_arm_expiry(self):
        """Check if armed duration has expired."""
        if self.is_armed and self.arm_time:
            elapsed = time.time() - self.arm_time
            if elapsed > self.arm_duration:
                logger.info("Arm duration expired - disarming")
                self.disarm()
    
    def disarm(self):
        """Disarm the agent."""
        self.is_armed = False
        self.armed_task = None
        self.arm_time = None
        logger.info("Agent DISARMED - hotkeys inactive")
    
    def consume_task(self, action_id):
        """Mark a task as consumed on the server."""
        try:
            data = {"id": action_id}
            headers = {"Content-Type": "application/json"}
            
            # Add HMAC headers if configured
            if self.hmac_secret:
                headers.update(self.get_hmac_headers(json.dumps(data)))
            
            response = requests.post(
                f"{self.server_url}/tasks/consume",
                json=data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Task {action_id} consumed successfully")
            else:
                logger.warning(f"Task consumption failed: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to consume task: {e}")
    
    def run(self):
        """Main agent loop."""
        logger.info("Zorder Agent started - polling for tasks...")
        
        # Check if ffmpeg is available
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         check=True)
            logger.info("FFmpeg found and working")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("FFmpeg not found - screen recording will not work")
            logger.error("Please install FFmpeg: winget install ffmpeg")
        
        try:
            while True:
                # Poll for tasks
                self.poll_tasks()
                
                # Check arm expiry
                if self.is_armed:
                    self.check_arm_expiry()
                
                # Wait before next poll
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            logger.info("Agent stopping...")
        except Exception as e:
            logger.error(f"Agent error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        try:
            # Stop recording if active
            if self.is_recording:
                self.stop_recording()
            
            # Stop keyboard listener
            if self.keyboard_listener:
                self.keyboard_listener.stop()
            
            logger.info("Agent cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

def main():
    """Main function."""
    print("Zorder Agent v1.0")
    print("==================")
    print("Global Hotkeys:")
    print("  F5 - Type username (when armed)")
    print("  F6 - Type password + Enter + Start recording (when armed)")
    print("  F7 - Stop recording early")
    print()
    print("Press Ctrl+C to stop")
    print()
    
    agent = ZorderAgent()
    agent.run()

if __name__ == "__main__":
    main()


