# Database Integration Guide

## 🎯 **Database Integration Status: ✅ COMPLETE**

Your Discord bot now has full MongoDB database integration with Base44 dashboard sync capabilities!

## 📊 **What's New:**

### ✅ **Database Features:**
- **MongoDB Integration**: Full async MongoDB support with Motor
- **Dynamic Prefixes**: Per-server command prefixes stored in database
- **Guild Settings**: Comprehensive server configuration management
- **Base44 Sync**: Automatic synchronization with Base44 dashboard
- **Error Handling**: Graceful fallbacks when database is unavailable
- **Auto Welcome**: Welcome messages and role assignment on member join

### ✅ **New Commands:**
- `!settings` - View current server settings
- `!prefix <new_prefix>` - Change bot command prefix
- `!welcome <message>` - Set welcome message for new members
- `!dbstatus` - Check database connection status
- `!sync` - Manually sync with Base44 dashboard

## 🚀 **Setup Instructions:**

### **Step 1: Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Step 2: Configure Database**
1. **MongoDB Atlas (Recommended):**
   - Create a free account at [MongoDB Atlas](https://www.mongodb.com/atlas)
   - Create a new cluster
   - Get your connection string
   - Update `config.env` with your MongoDB URI

2. **Local MongoDB:**
   - Install MongoDB locally
   - Use: `MONGO_URI=mongodb://localhost:27017/discord_bot_db`

### **Step 3: Update Environment Variables**
Edit your `config.env` file:
```env
# Database Configuration
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/discord_bot_db?retryWrites=true&w=majority
DB_NAME=discord_bot_db
```

### **Step 4: Test Database Integration**
```bash
python test_database.py
```

### **Step 5: Start Your Bot**
```bash
python start_bot.py
```

## 🗄️ **Database Schema:**

### **Guild Settings Collection:**
```json
{
  "guild_id": "123456789012345678",
  "prefix": "!",
  "welcome_message": "Welcome to the server!",
  "roles_on_join": ["9876543210"],
  "mod_log_channel": null,
  "auto_moderation": false,
  "created_at": "2024-01-01T00:00:00.000Z",
  "updated_at": "2024-01-01T00:00:00.000Z"
}
```

### **Field Descriptions:**
- `guild_id`: Discord server ID (unique identifier)
- `prefix`: Command prefix for this server
- `welcome_message`: Message sent to new members
- `roles_on_join`: Array of role IDs to assign automatically
- `mod_log_channel`: Channel ID for moderation logs
- `auto_moderation`: Enable/disable auto-moderation features
- `created_at`: Timestamp when settings were first created
- `updated_at`: Timestamp of last update

## 🔧 **How It Works:**

### **1. Dynamic Prefix System:**
```python
# Bot automatically fetches prefix from database for each guild
discord_bot = commands.Bot(command_prefix=get_prefix, intents=intents)

async def get_prefix(bot, message):
    guild_id = str(message.guild.id) if message.guild else "0"
    return await db_manager.get_prefix(guild_id)
```

### **2. Base44 Dashboard Sync:**
- Bot reads settings from Base44 API
- Updates local database with dashboard changes
- Maintains sync between dashboard and database
- Supports manual sync with `!sync` command

### **3. Error Handling:**
- Database connection failures use default settings
- Graceful degradation when MongoDB is unavailable
- Comprehensive logging for debugging

## 🎮 **Usage Examples:**

### **Setting Up a Server:**
```bash
# View current settings
!settings

# Change prefix
!prefix ?

# Set welcome message
!welcome Welcome {username} to {server_name}! Enjoy your stay!

# Check database status
!dbstatus

# Sync with Base44 dashboard
!sync
```

### **Programmatic Usage:**
```python
# Get guild settings
settings = await get_guild_settings("123456789012345678")

# Update settings
success = await update_guild_settings("123456789012345678", {
    "prefix": "?",
    "welcome_message": "New welcome message!"
})

# Get dynamic prefix
prefix = await get_prefix(bot, message)
```

## 🔍 **Monitoring & Debugging:**

### **Database Health Check:**
```python
health = await db_manager.health_check()
print(f"Connected: {health['connected']}")
print(f"Guilds: {health['guild_count']}")
```

### **Console Output:**
```
✅ Database connected successfully
📊 Database status: 3 guilds configured
  - My Server (ID: 123456789012345678)
    Settings: Prefix="!", Welcome="Welcome to the server!..."
```

### **Error Logging:**
- All database operations are logged
- Failed operations use safe defaults
- Comprehensive error messages for debugging

## 🛠️ **Advanced Configuration:**

### **Custom Default Settings:**
```python
# In database.py
self.default_guild_settings = {
    "prefix": "!",
    "welcome_message": "Welcome to the server!",
    "roles_on_join": [],
    "mod_log_channel": None,
    "auto_moderation": False,
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow()
}
```

### **Adding New Settings:**
1. Update `default_guild_settings` in `database.py`
2. Add getter/setter methods to `DatabaseManager`
3. Create Discord commands for the new settings
4. Update Base44 sync logic if needed

## 🚨 **Troubleshooting:**

### **Common Issues:**

#### **1. "Database not connected"**
- **Cause**: MongoDB URI not set or incorrect
- **Solution**: Check `MONGO_URI` in config.env
- **Action**: Bot continues with default settings

#### **2. "Failed to update settings"**
- **Cause**: Database connection lost
- **Solution**: Check MongoDB connection
- **Action**: Bot logs error and continues

#### **3. "Settings not syncing with Base44"**
- **Cause**: Base44 API issues
- **Solution**: Use `!sync` command manually
- **Action**: Check Base44 dashboard connectivity

### **Debug Commands:**
```bash
# Test database connection
python test_database.py

# Check environment variables
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('MONGO_URI:', 'SET' if os.getenv('MONGO_URI') else 'NOT SET')"

# Start bot with verbose logging
python start_bot.py
```

## 🎉 **You're All Set!**

Your Discord bot now has:
- ✅ **MongoDB Integration**: Full database support
- ✅ **Dynamic Settings**: Per-server configuration
- ✅ **Base44 Sync**: Dashboard integration
- ✅ **Auto Welcome**: Member join handling
- ✅ **Error Handling**: Graceful fallbacks
- ✅ **Monitoring**: Health checks and logging

### **Next Steps:**
1. **Configure MongoDB**: Set up your database
2. **Test Integration**: Run the test script
3. **Start Bot**: Launch with database support
4. **Configure Servers**: Use the new commands
5. **Monitor Performance**: Check database status

Your bot will now automatically sync with the Base44 dashboard and store all settings in the database for persistent, per-server configuration!
