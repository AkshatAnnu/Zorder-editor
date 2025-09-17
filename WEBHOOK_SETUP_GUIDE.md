# WhatsApp Webhook Setup Guide for Meta Dashboard

## 🚀 Complete Step-by-Step Guide

### Prerequisites
- Meta Developer Account
- WhatsApp Business API App
- Your Zorder server running locally
- ngrok installed (for local development)

---

## Step 1: Install ngrok (for local development)

### Option A: Download from website
1. Go to https://ngrok.com/download
2. Download ngrok for your OS
3. Extract and add to PATH

### Option B: Install via Homebrew (Mac)
```bash
brew install ngrok
```

### Option C: Install via package manager
```bash
# Ubuntu/Debian
sudo apt install ngrok

# Windows (Chocolatey)
choco install ngrok
```

---

## Step 2: Start ngrok tunnel

```bash
# Start ngrok tunnel to your local server
ngrok http 8000
```

**Important**: Keep this terminal open! You'll get a public URL like:
```
https://abc123.ngrok.io -> http://localhost:8000
```

---

## Step 3: Configure Meta Dashboard

### 3.1 Go to Meta for Developers
1. Visit https://developers.facebook.com/
2. Log in with your Facebook account
3. Go to "My Apps" → Select your WhatsApp Business API app

### 3.2 Navigate to WhatsApp Configuration
1. In your app dashboard, click on "WhatsApp" in the left sidebar
2. Click on "Configuration" tab

### 3.3 Set up Webhook
1. **Webhook URL**: Enter your ngrok URL + `/webhook/whatsapp`
   ```
   Example: https://abc123.ngrok.io/webhook/whatsapp
   ```

2. **Verify Token**: Enter your verification token
   ```
   zorder_verify_token_2024
   ```

3. **Webhook Fields**: Select the following fields:
   - ✅ `messages`
   - ✅ `message_deliveries`
   - ✅ `message_reads`
   - ✅ `message_reactions`

### 3.4 Verify Webhook
1. Click "Verify and Save"
2. Meta will send a GET request to your webhook
3. Your server should respond with the challenge string
4. If successful, you'll see "Webhook verified successfully"

---

## Step 4: Test Webhook Integration

### 4.1 Test Webhook Verification
```bash
# This should return the challenge string
curl "https://your-ngrok-url.ngrok.io/webhook/whatsapp?hub.mode=subscribe&hub.challenge=test123&hub.verify_token=zorder_verify_token_2024"
```

### 4.2 Test WhatsApp Message
```bash
# Send a test bill-edited event
curl -X POST https://your-ngrok-url.ngrok.io/event/bill-edited \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_id": "TEST-WEBHOOK-001",
    "biller_id": "BILLER-WEBHOOK-123",
    "machine_id": "DESKTOP-001",
    "admin_url": "https://admin.example.com/bill/TEST-WEBHOOK-001"
  }'
```

---

## Step 5: Production Setup (Optional)

For production, replace ngrok with:
- **Cloud hosting**: AWS, Google Cloud, Azure
- **Domain**: Your own domain with SSL certificate
- **Reverse proxy**: Nginx, Apache

### Production Webhook URL Example:
```
https://yourdomain.com/webhook/whatsapp
```

---

## Troubleshooting

### Issue 1: Webhook verification fails
**Solution**: 
- Check if your server is running
- Verify the ngrok URL is correct
- Ensure VERIFY_TOKEN matches exactly

### Issue 2: 401 Unauthorized
**Solution**:
- Get a fresh WhatsApp access token
- Update `WHATSAPP_TOKEN` in your `.env` file
- Restart your server

### Issue 3: ngrok URL changes
**Solution**:
- ngrok free tier changes URLs on restart
- Update webhook URL in Meta dashboard
- Consider ngrok paid plan for static URLs

### Issue 4: Webhook not receiving messages
**Solution**:
- Check webhook fields are selected
- Verify webhook URL is accessible
- Check server logs for errors

---

## Current Configuration

### Your Server Settings:
- **Local URL**: http://localhost:8000
- **Webhook Endpoint**: /webhook/whatsapp
- **Verify Token**: zorder_verify_token_2024
- **Phone ID**: 788846207647515
- **Owner Number**: 919643287594

### Environment Variables:
```env
WHATSAPP_TOKEN=your_token_here
WHATSAPP_PHONE_ID=788846207647515
OWNER_WA_NUMBER=919643287594
VERIFY_TOKEN=zorder_verify_token_2024
```

---

## Next Steps

1. ✅ Install ngrok
2. ✅ Start ngrok tunnel
3. ✅ Configure Meta dashboard
4. ✅ Test webhook verification
5. ✅ Test complete workflow
6. ✅ Deploy to production (optional)

---

## Support

If you encounter issues:
1. Check server logs: `tail -f server/logs/app.log`
2. Test endpoints individually
3. Verify all environment variables
4. Check Meta dashboard webhook status

**Your Zorder Bill Editor webhook will be ready once you complete these steps!** 🎉


