# Zorder Bill Editor

**WhatsApp Approval + Secure Autofill + 3-min Recording (Windows target, dev on Mac)**

A production-ready system for secure bill editing workflow with WhatsApp approvals, automated login, and screen recording capabilities.

## 🎯 Features

- **WhatsApp Integration**: Owner receives YES/NO approval buttons via WhatsApp Cloud API
- **Secure Autofill**: Dual-key encrypted credential storage with Windows Credential Manager
- **Screen Recording**: 3-minute desktop recording with ffmpeg (configurable duration)
- **Global Hotkeys**: F5 (username), F6 (password + enter + record), F7 (stop early)
- **Security-First**: No clipboard usage, HMAC signing, encrypted storage
- **Cross-Platform Dev**: Mac development, Windows agent deployment
- **Production Ready**: Logging, error handling, packaging, CI/CD

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Owner GUI     │    │   Flask Server  │    │ Windows Agent   │
│   (Console)     │    │   (Mac/Linux)   │    │  (Target PC)    │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Tkinter GUI   │───▶│ • REST API      │◀───│ • Global Hotkeys│
│ • Send Requests │    │ • SQLite DB     │    │ • Screen Record │
│ • .env Config   │    │ • WhatsApp API  │    │ • Encrypted Creds│
└─────────────────┘    │ • File Upload   │    │ • Auto Upload   │
                       └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  WhatsApp API   │
                       │ (Meta Business) │
                       ├─────────────────┤
                       │ • YES/NO Buttons│
                       │ • Media Upload  │
                       │ • Owner Notify  │
                       └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

**Mac (Development Server):**
- Python 3.11+
- WhatsApp Business API access
- ngrok (for webhook development)

**Windows (Agent):**
- Python 3.11+
- FFmpeg (`winget install ffmpeg`)

### 1. Server Setup (Mac)

```bash
# Clone and setup server
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your WhatsApp credentials

# Run server
python3 app.py
```

### 2. Public URL for WhatsApp Webhook

```bash
# In another terminal
ngrok http 8000
# Copy the https URL for WhatsApp webhook configuration
```

### 3. Console Setup (Mac)

```bash
cd console
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Set SERVER_URL to your server

# Run console
python3 console.py
```

### 4. Windows Agent Setup

```powershell
# Install Python 3.11 and FFmpeg
winget install Python.Python.3.11
winget install ffmpeg

# Setup agent
cd agent
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
# Edit .env with SERVER_URL and MACHINE_ID

# Setup credentials (one-time)
py secret_store.py
# Enter your login username/password

# Run agent
py agent.py
```

## 📋 Environment Configuration

### Server (.env)

```env
WHATSAPP_TOKEN=EAAM_your_permanent_access_token
WHATSAPP_PHONE_ID=123456789012345
OWNER_WA_NUMBER=91XXXXXXXXXX
VERIFY_TOKEN=your_webhook_verify_token
DB_PATH=data.db
UPLOAD_DIR=uploads
HMAC_SECRET=optional_hmac_secret
```

### Console (.env)

```env
SERVER_URL=http://127.0.0.1:8000
```

### Agent (.env)

```env
SERVER_URL=http://your-server-url:8000
MACHINE_ID=COUNTER-1
RECORD_DIR=C:\Recordings
RECORD_SECONDS=180
POLL_INTERVAL=5
ARM_DURATION=600
HMAC_SECRET=optional_hmac_secret
```

## 🔧 API Reference

### Server Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/healthz` | Simple health check |
| POST | `/event/bill-edited` | Trigger approval request |
| GET | `/webhook/whatsapp` | WhatsApp webhook verification |
| POST | `/webhook/whatsapp` | WhatsApp webhook receiver |
| GET | `/tasks/<machine_id>` | Get pending tasks |
| POST | `/tasks/consume` | Mark task as consumed |
| POST | `/upload/recording` | Upload screen recording |

### Bill Edit Request

```json
POST /event/bill-edited
{
  "invoice_id": "INV-001",
  "biller_id": "user@example.com",
  "machine_id": "COUNTER-1",
  "admin_url": "https://admin.example.com/bill/123"
}
```

## ⌨️ Hotkeys

| Key | Action | Condition |
|-----|--------|-----------|
| **F5** | Type username | Agent armed |
| **F6** | Type password + Enter + Start recording | Agent armed |
| **F7** | Stop recording early | Recording active |

## 🔒 Security Features

### Credential Protection
- **Dual-key encryption**: Username and password encrypted with separate Fernet keys
- **Windows Credential Manager**: Encryption keys stored securely
- **No clipboard usage**: Direct keystroke simulation only
- **File permissions**: Restrictive access to credential files

### Optional Security Enhancements
- **HMAC signing**: Request authentication between agent and server
- **Paste blocking**: Suppress Ctrl+V/Shift+Insert during autofill (TODO)
- **Audit logging**: Comprehensive logging without credential exposure

### Network Security
- **HTTPS required**: Production deployments must use HTTPS
- **Webhook verification**: WhatsApp webhook token validation
- **Request timeouts**: All HTTP requests have appropriate timeouts

## 📦 Packaging & Distribution

### Building Windows Executables

```bash
# On Windows with GitHub Actions or locally:
pip install pyinstaller

# Build agent
cd agent
pyinstaller --onefile --noconsole --name agent --distpath ../dist agent.py

# Build console
cd console
pyinstaller --onefile --windowed --name console --distpath ../dist console.py
```

### Inno Setup Installer

```bash
# Install Inno Setup, then:
iscc installer/zorder.iss
# Generates ZorderInstaller.exe
```

### Scheduled Task Installation

The installer automatically creates a Windows Scheduled Task:
- **Name**: ZorderAgent
- **Trigger**: At user logon
- **Security**: Run with highest privileges
- **Persistence**: Runs when user logs in

## 🚨 Troubleshooting

### Common Issues

**Agent not responding to hotkeys:**
- Check if agent is armed (needs approved task)
- Verify credentials are set: `py secret_store.py`
- Check agent logs: `zorder_agent.log`

**Recording not working:**
- Install FFmpeg: `winget install ffmpeg`
- Verify FFmpeg in PATH: `ffmpeg -version`
- Check recording directory permissions

**WhatsApp messages not sending:**
- Verify WHATSAPP_TOKEN and WHATSAPP_PHONE_ID
- Check webhook URL is accessible
- Review server logs: `zorder.log`

**Connection issues:**
- Test server connectivity from console
- Verify firewall/network settings
- Check server URL configuration

### Debug Mode

```bash
# Server debug mode
python3 app.py  # Debug enabled by default

# Agent verbose logging
# Edit agent.py and change logging level to DEBUG
```

## 🧪 Testing Flow

1. **Send approval request** (Console → Server)
2. **Receive WhatsApp message** with YES/NO buttons
3. **Click NO**: Agent remains disarmed
4. **Click YES**: Agent arms for 10 minutes
5. **Navigate to login page**
6. **Press F5**: Username typed
7. **Press F6**: Password typed, Enter pressed, recording starts
8. **Wait 3 minutes** or **press F7** to stop early
9. **Video uploads** and forwards to WhatsApp
10. **Agent disarms** automatically

## 🔄 CI/CD Pipeline

GitHub Actions automatically builds Windows executables on:
- Push to main branch
- Pull requests
- Manual workflow dispatch

Artifacts include:
- `agent.exe` - Windows agent executable
- `console.exe` - Console GUI executable
- `secret_store.exe` - Credential management tool
- Configuration examples and documentation

## 📝 Development

### Local Development Setup

```bash
# Server development
cd server && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 app.py

# Console development  
cd console && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 console.py

# Agent development (Windows)
cd agent && py -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
py agent.py
```

### Code Quality

- **Logging**: Comprehensive logging without credential exposure
- **Error Handling**: Graceful degradation and user-friendly error messages
- **Type Hints**: Modern Python typing where applicable
- **Documentation**: Inline comments and docstrings

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Create GitHub Issues for bugs/features
- Check troubleshooting section first
- Include log files when reporting issues

---

**⚠️ Important Security Notes:**
- Always use HTTPS in production
- Regularly rotate WhatsApp tokens
- Monitor access logs
- Implement proper backup procedures
- Staff consent required for screen recording
- Consider data retention policies


