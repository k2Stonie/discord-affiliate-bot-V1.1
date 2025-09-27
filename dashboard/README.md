# Discord Affiliate Bot Dashboard

A modern, MEE6-style web dashboard for managing your Discord Affiliate Bot with Discord OAuth2 authentication.

## ✨ Features

- **Discord OAuth2 Login**: Secure authentication with your Discord account
- **Modern UI**: Beautiful, responsive design inspired by MEE6
- **Real-time Updates**: Live bot status and activity monitoring via WebSocket
- **Server Management**: View and manage connected Discord servers
- **Campaign Management**: Create and manage marketing campaigns
- **Analytics Dashboard**: View detailed statistics and activity charts
- **Bot Settings**: Configure bot preferences and behavior
- **Target Role Management**: Set up role-based targeting for campaigns

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Discord bot token and OAuth2 credentials
- MongoDB database (optional, for persistent storage)

### Installation

1. **Navigate to the dashboard directory**
   ```bash
   cd dashboard
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   - Copy `../config.env` to the dashboard directory
   - Ensure all required variables are set:
     ```env
     # Discord Configuration
     DISCORD_BOT_TOKEN=your_bot_token_here
     DISCORD_CLIENT_ID=your_client_id_here
     DISCORD_CLIENT_SECRET=your_client_secret_here
     DISCORD_REDIRECT_URI=http://localhost:5000/callback
     
     # Database Configuration
     MONGO_URI=your_mongodb_connection_string
     DB_NAME=discord_bot_db
     
     # Base44 Configuration
     BASE44_APP_ID=your_base44_app_id
     BASE44_FUNCTION_TOKEN=your_base44_token
     API_BASE_URL=https://app.base44.com/api/
     ```

4. **Run the dashboard**
   ```bash
   python run_dashboard.py
   ```

5. **Access the dashboard**
   - Open your browser and go to: `http://localhost:5000`
   - Click "Login with Discord" to authenticate
   - Start managing your bot!

## 🎛️ Dashboard Sections

### Overview
- Bot status and connection information
- Server count and member statistics
- Activity charts and recent activity
- Quick access to key functions

### Server Management
- View all connected Discord servers
- Server details and bot permissions
- Server-specific settings and configuration
- Real-time server status updates

### Campaign Management
- Create and manage marketing campaigns
- Target specific roles with custom messages
- Campaign performance tracking
- Message template management

### Analytics
- Detailed statistics and metrics
- Activity charts and trends
- Message delivery statistics
- Campaign performance analysis

### Settings
- Bot configuration and preferences
- Welcome message customization
- Auto-moderation settings
- Integration management

## 🔧 Configuration

### Discord OAuth2 Setup

1. **Create Discord Application**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Note your Client ID and Client Secret

2. **Configure OAuth2**
   - Go to OAuth2 section
   - Add redirect URI: `http://localhost:5000/callback`
   - Select scopes: `identify`, `guilds`

3. **Update Configuration**
   - Set `DISCORD_CLIENT_ID` and `DISCORD_CLIENT_SECRET` in your config
   - Ensure `DISCORD_REDIRECT_URI` matches your OAuth2 settings

### Database Configuration

The dashboard supports MongoDB for persistent storage:

```env
MONGO_URI=mongodb://localhost:27017/discord_bot_db
DB_NAME=discord_bot_db
```

For MongoDB Atlas:
```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/discord_bot_db
DB_NAME=discord_bot_db
```

## 📁 File Structure

```
dashboard/
├── app.py                 # Main Flask application
├── run_dashboard.py       # Dashboard runner script
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── login.html        # Login page
│   └── dashboard.html    # Main dashboard
├── static/               # Static assets
│   ├── css/
│   │   └── dashboard.css # Dashboard styles
│   └── js/
│       └── dashboard.js  # Dashboard JavaScript
└── config.env           # Configuration file
```

## 🔌 API Endpoints

### Authentication
- `GET /` - Main dashboard page
- `GET /login` - Initiate Discord OAuth2 login
- `GET /callback` - OAuth2 callback handler
- `GET /logout` - Logout user

### API Routes
- `GET /api/guilds` - Get user's guilds
- `GET /api/guild/<guild_id>` - Get guild details
- `GET/POST /api/guild/<guild_id>/settings` - Manage guild settings
- `GET /api/analytics` - Get bot analytics
- `GET/POST /api/campaigns/<guild_id>` - Manage campaigns

### WebSocket Events
- `connect` - Client connection
- `disconnect` - Client disconnection
- `join_guild` - Join guild room for updates
- `leave_guild` - Leave guild room
- `bot_status_update` - Bot status changes
- `guild_joined` - Bot joined a server
- `guild_left` - Bot left a server
- `settings_updated` - Settings changed

## 🎨 Customization

### Styling
The dashboard uses CSS custom properties for easy theming:

```css
:root {
    --primary-color: #5865F2;
    --secondary-color: #747F8D;
    --success-color: #3BA55C;
    --warning-color: #FAA61A;
    --danger-color: #ED4245;
}
```

### Adding New Features
1. Add new routes in `app.py`
2. Create corresponding templates in `templates/`
3. Add JavaScript functionality in `static/js/dashboard.js`
4. Update navigation in `templates/base.html`

## 🔒 Security

- **OAuth2 Authentication**: Secure Discord login
- **Session Management**: Secure session handling
- **CSRF Protection**: Built-in CSRF protection
- **Input Validation**: All inputs are validated and sanitized
- **HTTPS Ready**: Configure for HTTPS in production

## 🚀 Deployment

### Local Development
```bash
python run_dashboard.py
```

### Production Deployment
1. Set `FLASK_ENV=production`
2. Configure HTTPS and SSL certificates
3. Use a production WSGI server (Gunicorn, uWSGI)
4. Set up reverse proxy (Nginx, Apache)
5. Configure environment variables securely

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "run_dashboard.py"]
```

## 🐛 Troubleshooting

### Common Issues

1. **OAuth2 Redirect URI Mismatch**
   - Ensure redirect URI in Discord app matches `DISCORD_REDIRECT_URI`
   - Check for trailing slashes and protocol (http/https)

2. **Database Connection Issues**
   - Verify MongoDB connection string
   - Check network connectivity
   - Ensure database permissions

3. **Bot Not Connecting**
   - Verify bot token is correct
   - Check bot permissions in Discord
   - Ensure bot is invited to servers

4. **WebSocket Connection Issues**
   - Check firewall settings
   - Verify SocketIO configuration
   - Check browser console for errors

### Debug Mode
Enable debug mode for detailed error information:

```python
app.config['DEBUG'] = True
```

## 📊 Monitoring

The dashboard includes built-in monitoring:
- Bot status and health checks
- Database connection monitoring
- WebSocket connection status
- Error logging and reporting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is for educational and personal use.

## 🆘 Support

If you encounter any issues:
1. Check the console output for errors
2. Verify your configuration
3. Check the troubleshooting section
4. Create an issue with detailed information

---

**Made with ❤️ for Discord communities**
