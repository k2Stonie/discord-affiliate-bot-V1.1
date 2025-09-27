#!/usr/bin/env python3
"""
Discord Affiliate Bot Dashboard
A modern web dashboard for managing the Discord affiliate bot with Discord OAuth2 authentication.
"""

import os
import asyncio
import threading
import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import urllib.parse
import aiohttp
import aiofiles
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_socketio import SocketIO, emit, join_room, leave_room
import discord
from discord.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

try:
    from bot import notify_guild_update
except ImportError:
    def notify_guild_update(guild_id: str):
        pass


# Load environment variables
load_dotenv('../config.env')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Discord OAuth2 configuration
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
DISCORD_REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI', 'http://localhost:5000/callback')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Database configuration
MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('DB_NAME', 'discord_bot_db')

# Base44 configuration
BASE44_APP_ID = os.getenv('BASE44_APP_ID')
BASE44_FUNCTION_TOKEN = os.getenv('BASE44_FUNCTION_TOKEN')
API_BASE_URL = os.getenv('API_BASE_URL')

# Global variables
mongo_client = None
bot_instance = None
connected_guilds = {}

class DashboardManager:
    """Manages dashboard operations and bot communication."""
    
    def __init__(self):
        self.mongo_client = None
        self.db = None
        self.bot_instance = None
        self.connected_guilds = {}
        self.bot_thread = None
        self.bot_ready_event = threading.Event()
        
    def initialize(self):
        """Initialize database connection and bot instance."""
        try:
            # Initialize MongoDB connection
            if MONGO_URI:
                self.mongo_client = MongoClient(MONGO_URI)
                self.db = self.mongo_client[DB_NAME]
                logger.info("✅ Connected to MongoDB")
            else:
                logger.warning("⚠️ No MongoDB URI provided")
                
            # Initialize Discord bot in background thread
            self._start_discord_bot()
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize dashboard: {e}")
    
    def _setup_bot_events(self):
        """Setup Discord bot event handlers."""
        
        @self.bot_instance.event
        async def on_ready():
            logger.info(f"🤖 Bot logged in as {self.bot_instance.user}")
            self.connected_guilds = {guild.id: guild for guild in self.bot_instance.guilds}
            self.bot_ready_event.set()
            
            # Emit bot status update to dashboard
            socketio.emit('bot_status_update', {
                'status': 'online',
                'guild_count': len(self.bot_instance.guilds),
                'guilds': [{'id': str(g.id), 'name': g.name} for g in self.bot_instance.guilds]
            })
        
        @self.bot_instance.event
        async def on_guild_join(guild):
            self.connected_guilds[guild.id] = guild
            socketio.emit('guild_joined', {
                'id': str(guild.id),
                'name': guild.name,
                'member_count': guild.member_count
            })
        
        @self.bot_instance.event
        async def on_guild_remove(guild):
            if guild.id in self.connected_guilds:
                del self.connected_guilds[guild.id]
            socketio.emit('guild_left', {'id': str(guild.id), 'name': guild.name})

    def _start_discord_bot(self):
        """Start the Discord bot in a background thread."""
        if not DISCORD_BOT_TOKEN:
            logger.error("❌ Discord bot token is not configured. Set DISCORD_BOT_TOKEN in config.env")
            return

        if self.bot_thread and self.bot_thread.is_alive():
            logger.debug("Discord bot thread already running")
            return

        self.bot_ready_event.clear()

        def run_bot():
            async def bot_main():
                try:
                    intents = discord.Intents.all()
                    self.bot_instance = commands.Bot(command_prefix='!', intents=intents)
                    self._setup_bot_events()
                    await self.bot_instance.start(DISCORD_BOT_TOKEN)
                except Exception as e:
                    logger.error(f"❌ Discord bot terminated unexpectedly: {e}")

            asyncio.run(bot_main())

        self.bot_thread = threading.Thread(target=run_bot, name='DashboardDiscordBot', daemon=True)
        self.bot_thread.start()
        # Wait briefly for the bot to be ready
        if not self.bot_ready_event.wait(timeout=30):
            logger.warning("⚠️ Discord bot did not become ready within 30 seconds")
    
    def get_guild_data(self, guild_id: str) -> Dict[str, Any]:
        """Get comprehensive guild data for dashboard."""
        try:
            guild = self.connected_guilds.get(int(guild_id))
            if not guild:
                return {'error': 'Guild not found'}
            
            # Get database settings
            settings = {}
            if self.db is not None:
                settings_doc = self.db.guild_settings.find_one({'guild_id': guild_id})
                if settings_doc:
                    settings = settings_doc
            
            return {
                'id': str(guild.id),
                'name': guild.name,
                'icon': str(guild.icon.url) if guild.icon else None,
                'member_count': guild.member_count,
                'owner_id': str(guild.owner_id),
                'created_at': guild.created_at.isoformat(),
                'roles': [
                    {
                        'id': str(role.id),
                        'name': role.name,
                        'color': str(role.color),
                        'position': role.position,
                        'managed': role.managed,
                        'mentionable': role.mentionable
                    }
                    for role in sorted(guild.roles, key=lambda r: r.position, reverse=True)
                ],
                'channels': [
                    {
                        'id': str(channel.id),
                        'name': channel.name,
                        'type': str(channel.type),
                        'position': getattr(channel, 'position', 0)
                    }
                    for channel in guild.channels
                ],
                'settings': settings,
                'bot_permissions': {
                    'administrator': guild.me.guild_permissions.administrator,
                    'manage_guild': guild.me.guild_permissions.manage_guild,
                    'manage_roles': guild.me.guild_permissions.manage_roles,
                    'send_messages': guild.me.guild_permissions.send_messages,
                    'manage_messages': guild.me.guild_permissions.manage_messages
                }
            }
        except Exception:
            logger.exception("Error getting guild data")
            return {'error': 'Failed to load guild data'}
    
    def update_guild_settings(self, guild_id: str, settings: Dict[str, Any]) -> bool:
        """Update guild settings in database."""
        try:
            if self.db is None:
                return False

            settings['guild_id'] = guild_id
            settings['updated_at'] = datetime.utcnow()

            self.db.guild_settings.update_one(
                {'guild_id': guild_id},
                {'$set': settings},
                upsert=True
            )
            
            # Emit update to dashboard
            socketio.emit('settings_updated', {
                'guild_id': guild_id,
                'settings': settings
            })
            
            return True
        except Exception as e:
            logger.error(f"Error updating guild settings: {e}")
            return False
    
    def get_bot_analytics(self, guild_id: str = None) -> Dict[str, Any]:
        """Get bot analytics and statistics."""
        try:
            analytics = {
                'total_guilds': len(self.connected_guilds),
                'total_members': sum(g.member_count for g in self.connected_guilds.values()),
                'uptime': datetime.utcnow().isoformat(),
                'guild_analytics': {}
            }
            
            if guild_id and self.db is not None:
                # Get guild-specific analytics
                activities = list(
                    self.db.bot_activities
                    .find({'server_id': guild_id})
                    .sort('timestamp', -1)
                    .limit(100)
                )
                
                analytics['guild_analytics'][guild_id] = {
                    'total_activities': len(activities),
                    'recent_activities': activities[:10],
                    'message_sent_count': len([a for a in activities if a.get('event_type') == 'message_sent']),
                    'welcome_messages': len([a for a in activities if a.get('event_type') == 'welcome_message_sent']),
                    'role_assignments': len([a for a in activities if a.get('event_type') == 'auto_role_assigned'])
                }
            
            return analytics
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {'error': str(e)}

    async def broadcast_settings(self, guild_id: str, settings: Dict[str, Any]):
        socketio.emit('settings_updated', {
            'guild_id': guild_id,
            'settings': settings
        }, room=f"guild_{guild_id}")

# Initialize dashboard manager
dashboard_manager = DashboardManager()

# Discord OAuth2 routes
@app.route('/')
async def index():
    """Main dashboard page."""
    if 'user' not in session:
        return render_template('login.html')
    
    return render_template('dashboard.html', user=session['user'])

@app.route('/login')
def login():
    """Initiate Discord OAuth2 login."""
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    discord_auth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify%20guilds"
        f"&state={state}"
    )
    
    return redirect(discord_auth_url)

@app.route('/callback')
async def callback():
    """Handle Discord OAuth2 callback."""
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code or state != session.get('oauth_state'):
        flash('Invalid OAuth2 state', 'error')
        return redirect(url_for('index'))
    
    try:
        # Exchange code for access token
        async with aiohttp.ClientSession() as session_client:
            token_data = {
                'client_id': DISCORD_CLIENT_ID,
                'client_secret': DISCORD_CLIENT_SECRET,
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': DISCORD_REDIRECT_URI
            }
            
            async with session_client.post('https://discord.com/api/oauth2/token', data=token_data) as resp:
                if resp.status != 200:
                    flash('Failed to exchange code for token', 'error')
                    return redirect(url_for('index'))
                
                token_info = await resp.json()
                access_token = token_info['access_token']
            
            # Get user info
            headers = {'Authorization': f'Bearer {access_token}'}
            async with session_client.get('https://discord.com/api/users/@me', headers=headers) as resp:
                if resp.status != 200:
                    flash('Failed to get user info', 'error')
                    return redirect(url_for('index'))
                
                user_info = await resp.json()
            
            # Get user's guilds
            async with session_client.get('https://discord.com/api/users/@me/guilds', headers=headers) as resp:
                if resp.status == 200:
                    user_guilds = await resp.json()
                    # Filter guilds where user has admin permissions
                    admin_guilds = [
                        guild for guild in user_guilds
                        if int(guild['permissions']) & 0x8  # Administrator permission
                    ]
                    user_info['guilds'] = admin_guilds
            
            # Store user info in session
            session['user'] = user_info
            session['access_token'] = access_token
            session.permanent = True
            
            flash('Successfully logged in!', 'success')
            return redirect(url_for('index'))
    
    except Exception as e:
        logger.error(f"OAuth2 callback error: {e}")
        flash('Authentication failed', 'error')
        return redirect(url_for('index'))

@app.route('/invite/<guild_id>')
async def invite_bot(guild_id):
    """Redirect to Discord OAuth invitation"""
    if 'user' not in session:
        flash('Please log in to invite the bot', 'warning')
        return redirect(url_for('login'))

    redirect_uri = urllib.parse.quote_plus(DISCORD_REDIRECT_URI)
    invite_url = (
        "https://discord.com/api/oauth2/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        "&scope=bot%20applications.commands"
        "&permissions=2147483647"
        f"&guild_id={guild_id}"
        "&disable_guild_select=true"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
    )

    return redirect(invite_url)

@app.route('/logout')
def logout():
    """Logout user."""
    session.clear()
    flash('Successfully logged out', 'info')
    return redirect(url_for('index'))

# API Routes
@app.route('/api/guilds')
async def api_guilds():
    """Get list of user's guilds."""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_guilds = session['user'].get('guilds', [])
    bot_guilds = list(dashboard_manager.connected_guilds.values())

    PERMISSION_ADMIN = 0x8
    PERMISSION_MANAGE_SERVER = 0x20

    filtered_guilds = []
    for g in user_guilds:
        perms = int(g.get('permissions', 0))
        if perms & (PERMISSION_ADMIN | PERMISSION_MANAGE_SERVER):
            filtered_guilds.append(g)

    # Match filtered guilds with bot guilds
    matched_guilds = []
    for user_guild in filtered_guilds:
        for bot_guild in bot_guilds:
            if str(user_guild['id']) == str(bot_guild.id):
                member_label = f"{bot_guild.member_count} members"
                role_label = 'Owner' if user_guild.get('owner') else 'Admin'
                matched_guilds.append({
                    'id': str(bot_guild.id),
                    'name': bot_guild.name,
                    'icon': str(bot_guild.icon.url) if bot_guild.icon else None,
                    'member_count': bot_guild.member_count,
                    'bot_connected': True,
                    'role_label': role_label,
                    'member_label': member_label
                })
                break
        else:
            member_label = 'Setup'
            role_label = 'Owner' if user_guild.get('owner') else 'Admin'
            matched_guilds.append({
                'id': str(user_guild['id']),
                'name': user_guild['name'],
                'icon': f"https://cdn.discordapp.com/icons/{user_guild['id']}/{user_guild['icon']}.png" if user_guild.get('icon') else None,
                'member_count': 0,
                'bot_connected': False,
                'role_label': role_label,
                'member_label': member_label
            })
    
    return jsonify({'guilds': matched_guilds})

@app.route('/api/guild/<guild_id>')
async def api_guild(guild_id):
    """Get detailed guild information."""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    loop = asyncio.get_running_loop()
    guild_data = await loop.run_in_executor(None, dashboard_manager.get_guild_data, guild_id)
    return jsonify(guild_data)

@app.route('/api/guild/<guild_id>/settings', methods=['GET', 'POST'])
async def api_guild_settings(guild_id):
    """Get or update guild settings."""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if request.method == 'GET':
        if dashboard_manager.db is not None:
            loop = asyncio.get_running_loop()
            settings = await loop.run_in_executor(
                None,
                dashboard_manager.db.guild_settings.find_one,
                {'guild_id': guild_id}
            )
            return jsonify(settings or {})
        return jsonify({})
    
    elif request.method == 'POST':
        settings = request.get_json() or {}
        settings.setdefault('guild_id', guild_id)
        loop = asyncio.get_running_loop()
        success = await loop.run_in_executor(None, dashboard_manager.update_guild_settings, guild_id, settings)

        if success:
            await dashboard_manager.broadcast_settings(guild_id, settings)
            notify_guild_update(guild_id)

        return jsonify({'success': success})

@app.route('/api/analytics')
async def api_analytics():
    """Get bot analytics."""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    guild_id = request.args.get('guild_id')
    loop = asyncio.get_running_loop()
    analytics = await loop.run_in_executor(None, dashboard_manager.get_bot_analytics, guild_id)
    return jsonify(analytics)

@app.route('/api/campaigns/<guild_id>', methods=['GET', 'POST'])
async def api_campaigns(guild_id):
    """Manage campaigns for a guild."""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if request.method == 'GET':
        if dashboard_manager.db is not None:
            loop = asyncio.get_running_loop()
            settings = await loop.run_in_executor(
                None,
                dashboard_manager.db.guild_settings.find_one,
                {'guild_id': guild_id}
            )
            campaigns = settings.get('campaigns', []) if settings else []
            return jsonify({'campaigns': campaigns})
        return jsonify({'campaigns': []})
    
    elif request.method == 'POST':
        campaign_data = request.get_json()
        loop = asyncio.get_running_loop()
        success = await loop.run_in_executor(None, dashboard_manager.update_guild_settings, guild_id, {'campaigns': [campaign_data]})
        return jsonify({'success': success})

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('join_guild')
def handle_join_guild(data):
    """Join a guild room for real-time updates."""
    guild_id = data.get('guild_id')
    if guild_id:
        join_room(f"guild_{guild_id}")
        emit('joined_guild', {'guild_id': guild_id})

@socketio.on('leave_guild')
def handle_leave_guild(data):
    """Leave a guild room."""
    guild_id = data.get('guild_id')
    if guild_id:
        leave_room(f"guild_{guild_id}")
        emit('left_guild', {'guild_id': guild_id})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# Initialize dashboard
def initialize_dashboard():
    """Initialize the dashboard manager."""
    dashboard_manager.initialize()

if __name__ == '__main__':
    # Determine whether to initialize (works with or without the reloader)
    run_main = os.environ.get('WERKZEUG_RUN_MAIN')
    if run_main == 'true' or run_main is None:
        initialize_dashboard()

    # Start Flask app without the reloader to avoid Windows socket errors
    socketio.run(
        app,
        debug=True,
        host='0.0.0.0',
        port=5000,
        use_reloader=False
    )
