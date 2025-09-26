#!/usr/bin/env python3
import discord
from discord.ext import commands
import asyncio
import aiohttp
import os
import time
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv

# Import database functionality
from database import (
    db_manager, get_prefix, get_guild_settings, update_guild_settings,
    init_database, close_database
)

# Ensure environment variables are loaded from config.env when present
load_dotenv('config.env')

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
BOT_ID = os.getenv('BASE44_APP_ID', '68d1f85a602cecfca6c02c10')
API_BASE_URL = os.getenv('API_BASE_URL', 'https://base44.app/api/apps/68d1f85a602cecfca6c10/functions')

if not DISCORD_BOT_TOKEN:
    print(' Error: DISCORD_BOT_TOKEN environment variable is required!')
    exit(1)

intents = discord.Intents.all()
# Use dynamic prefix function that fetches from database
discord_bot = commands.Bot(command_prefix=get_prefix, intents=intents)

class Base44Client:
    def __init__(self, api_base_url):
        self.api_base_url = api_base_url
        self.session = None
    
    async def call_function(self, function_name, payload=None):
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            url = f'{self.api_base_url}/{function_name}'
            
            # Get Base44 function token from environment
            import os
            from dotenv import load_dotenv
            load_dotenv('config.env')
            base44_token = os.getenv('BASE44_FUNCTION_TOKEN', '')
            
            headers = {
                'Content-Type': 'application/json', 
                'User-Agent': 'DiscordBot/1.0',
                'Authorization': f'Bearer {base44_token}'
            }
            async with self.session.post(url, json=payload or {}, headers=headers) as response:
                if response.status == 200:
                    # Try to parse as JSON first
                    try:
                        return await response.json()
                    except Exception as json_error:
                        # If JSON parsing fails, try to get text response
                        try:
                            text_response = await response.text()
                            print(f' API returned text instead of JSON: {text_response[:100]}...')
                            # Return a success response for text responses
                            return {"success": True, "message": text_response}
                        except Exception as text_error:
                            print(f' Failed to parse both JSON and text: {text_error}')
                            return None
                else:
                    print(f' API call failed: {function_name} - Status: {response.status}')
                    if response.status == 500:
                        print(f'  → Base44 endpoint may not be configured yet. This is normal for new setups.')
                    return None
        except Exception as e:
            print(f' Error calling {function_name}: {e}')
            return None
    
    async def get_bot_config(self, bot_id, bot_token, server_id=None):
        # Use the first guild's ID if no server_id provided
        if not server_id and discord_bot.guilds:
            server_id = str(discord_bot.guilds[0].id)
        
        payload = {
            "action": "getBotConfig",
            "payload": {
                "serverId": server_id
            }
        }
        return await self.call_function('botConfigManager', payload)
    
    async def log_bot_activity(self, activity_data):
        payload = {
            "action": "logBotActivity",
            "payload": {
                "activity": activity_data
            }
        }
        return await self.call_function('botConfigManager', payload)
    
    async def update_bot_status(self, status_data, config_id=None):
        payload = {
            "action": "updateBotStatus",
            "payload": {
                "configId": config_id or "default",
                "status": status_data.get('status', 'online')
            }
        }
        return await self.call_function('botConfigManager', payload)
    
    async def close(self):
        if self.session:
            await self.session.close()

class BotRateLimiter:
    def __init__(self):
        self.last_dm_time = {}
        self.rate_limit_delay = 1.0
    
    async def send_dm_safely(self, user, content, buttons=None):
        try:
            user_id = str(user.id)
            current_time = time.time()
            if user_id in self.last_dm_time:
                time_since_last = current_time - self.last_dm_time[user_id]
                if time_since_last < self.rate_limit_delay:
                    await asyncio.sleep(self.rate_limit_delay - time_since_last)
            self.last_dm_time[user_id] = time.time()
            if buttons:
                view = create_button_view(buttons)
                await user.send(content, view=view)
            else:
                await user.send(content)
            return True, None
        except discord.Forbidden:
            return False, 'User has DMs disabled'
        except discord.HTTPException as e:
            return False, f'HTTP Error: {str(e)}'
        except Exception as e:
            return False, f'Unknown error: {str(e)}'

class AffiliateBot:
    def __init__(self, bot_token, api_base_url, bot_id):
        self.bot_token = bot_token
        self.api_base_url = api_base_url
        self.bot_id = bot_id
        self.rate_limiter = BotRateLimiter()
        self.base44_client = Base44Client(api_base_url)
        self.current_config = None
        
    async def get_bot_config(self):
        try:
            # Get server_id from first guild
            server_id = str(discord_bot.guilds[0].id) if discord_bot.guilds else None
            config = await self.base44_client.get_bot_config(self.bot_id, self.bot_token, server_id)
            if config and config.get('success'):
                self.current_config = config.get('data', {})
                # Store config_id for status updates
                self.config_id = config.get('data', {}).get('id')
                
                # Sync Base44 config to database for all guilds
                for guild in discord_bot.guilds:
                    try:
                        await db_manager.sync_from_base44(str(guild.id), self.current_config)
                    except Exception as e:
                        print(f' Error syncing config for guild {guild.id}: {e}')
                
                return self.current_config
            else:
                print(' Failed to get bot config from Base44 platform - using default config')
                # Return a default configuration if Base44 is not available
                self.current_config = {
                    'active': True,
                    'affiliate_id': 'default_affiliate',
                    'message_templates': [],
                    'target_roles': [],
                    'affiliate_links': []
                }
                return self.current_config
        except Exception as e:
            print(f' Error getting bot config: {e} - using default config')
            # Return a default configuration if there's an error
            self.current_config = {
                'active': True,
                'affiliate_id': 'default_affiliate',
                'message_templates': [],
                'target_roles': [],
                'affiliate_links': []
            }
            return self.current_config
    
    async def log_bot_activity(self, activity_type, **kwargs):
        try:
            # Get server_id from kwargs or use first guild
            server_id = kwargs.get('guild_id', str(discord_bot.guilds[0].id) if discord_bot.guilds else 'unknown')
            
            activity_data = {
                'server_id': server_id,
                'event_type': activity_type,
                'details': {k: v for k, v in kwargs.items() if k not in ['guild_id', 'user_id']},
                'user_id': kwargs.get('user_id', 'unknown')
            }
            
            # Log to Base44 dashboard
            result = await self.base44_client.log_bot_activity(activity_data)
            if result and result.get('success'):
                print(f' Logged activity: {activity_type}')
            else:
                print(f' Failed to log activity: {activity_type}')
            
            # Also log to database if available
            try:
                if db_manager.is_connected:
                    # Create activity log collection
                    activity_collection = db_manager.db.bot_activities
                    await activity_collection.insert_one(activity_data)
            except Exception as db_error:
                print(f' Database logging error: {db_error}')
                
        except Exception as e:
            print(f' Error logging activity: {e}')
    
    async def update_bot_status(self, status, message=None, stats=None):
        try:
            status_data = {
                'bot_id': self.bot_id,
                'status': status,
                'message': message,
                'stats': stats or {}
            }
            result = await self.base44_client.update_bot_status(status_data)
            if result and result.get('success'):
                print(f' Updated bot status: {status}')
            else:
                print(f' Failed to update status: {status}')
        except Exception as e:
            print(f' Error updating status: {e}')
    
    def process_message_template(self, template, user, affiliate_id):
        content = template['content']
        content = content.replace('{username}', user.display_name)
        content = content.replace('{user_mention}', user.mention)
        content = content.replace('{affiliate_id}', str(affiliate_id))
        content = content.replace('{server_name}', user.guild.name if user.guild else 'Unknown Server')
        return content
    
    async def get_users_by_roles(self, guild, target_roles):
        valid_users = []
        enabled_role_ids = [role['role_id'] for role in target_roles if role['enabled']]
        for member in guild.members:
            if any(str(role.id) in enabled_role_ids for role in member.roles):
                valid_users.append(member)
        return valid_users
    
    def select_message_variant(self, user_id, ab_tests):
        if not ab_tests:
            return None
        user_hash = hash(user_id) % 2
        return 'A' if user_hash == 0 else 'B'
    
    def create_trackable_link(self, original_url, affiliate_id, campaign_id):
        tracking_code = f'{affiliate_id}_{campaign_id}_{int(time.time())}'
        return f'{self.api_base_url}/apps/{self.bot_id}/functions/affiliateManager?action=trackLinkClick&linkCode={tracking_code}'
    
    async def process_campaign(self, template, config):
        try:
            target_users = []
            for guild in discord_bot.guilds:
                users = await self.get_users_by_roles(guild, config.get('target_roles', []))
                target_users.extend(users)
            print(f' Found {len(target_users)} target users')
            for user in target_users:
                try:
                    variant = self.select_message_variant(str(user.id), template.get('ab_tests', []))
                    content = self.process_message_template(template, user, config.get('affiliate_id', 'default'))
                    buttons = None
                    if template.get('has_buttons', False):
                        buttons = []
                        for label in template.get('button_labels', []):
                            link_name = template.get('selected_link_name', 'main_affiliate_link')
                            original_url = next(
                                (link['url_template'] for link in config.get('affiliate_links', []) 
                                 if link['name'] == link_name), 
                                '#'
                            )
                            trackable_url = self.create_trackable_link(
                                original_url, 
                                config.get('affiliate_id', 'default'), 
                                template['name']
                            )
                            buttons.append({
                                'label': label,
                                'url': trackable_url,
                                'style': 'primary'
                            })
                    success, error = await self.rate_limiter.send_dm_safely(user, content, buttons)
                    await self.log_bot_activity('message_sent',
                        user_id=str(user.id),
                        message_sent=content,
                        role_targeted=config.get('target_roles', [{}])[0].get('role_name', 'Unknown') 
                        if config.get('target_roles') else 'Unknown',
                        success=success,
                        error_message=error if not success else None,
                        variant=variant
                    )
                    if success:
                        print(f' Sent DM to {user.display_name}')
                    else:
                        print(f' Failed to send DM to {user.display_name}: {error}')
                except Exception as e:
                    print(f' Error processing user {user.display_name}: {e}')
                    await self.log_bot_activity('error',
                        error_message=str(e),
                        success=False
                    )
        except Exception as e:
            print(f' Error processing campaign: {e}')
            await self.log_bot_activity('error',
                error_message=str(e),
                success=False
            )
    
    async def main_loop(self):
        while True:
            try:
                config = await self.get_bot_config()
                if not config.get('active', False):
                    print(' Bot is paused, waiting...')
                    await asyncio.sleep(60)
                    continue
                print(' Processing bot configuration from Base44 platform...')
                templates = config.get('message_templates', [])
                if templates:
                    for template in templates:
                        await self.process_campaign(template, config)
                    print(f' Processed {len(templates)} message templates')
                else:
                    print(' No message templates configured yet - bot is ready and waiting')
                
                await self.update_bot_status({
                    'status': 'active', 
                    'message': 'Bot running smoothly',
                    'stats': {
                        'messages_sent': len(templates),
                        'templates_configured': len(templates)
                    }
                }, self.config_id)
                print(' Waiting 5 minutes before next cycle...')
                await asyncio.sleep(300)
            except Exception as e:
                print(f' Error in main loop: {e}')
                await self.log_bot_activity('error', error_message=str(e), success=False)
                await asyncio.sleep(60)
    
    async def close(self):
        await self.base44_client.close()

def create_button_view(buttons):
    view = discord.ui.View()
    for button_data in buttons:
        button = discord.ui.Button(
            label=button_data['label'],
            url=button_data['url'],
            style=getattr(discord.ButtonStyle, button_data.get('style', 'primary'))
        )
        view.add_item(button)
    return view

affiliate_bot = AffiliateBot(DISCORD_BOT_TOKEN, API_BASE_URL, BOT_ID)

@discord_bot.event
async def on_ready():
    print(f' Logged in as {discord_bot.user}')
    print(f' Bot is in {len(discord_bot.guilds)} server(s)')
    print(f' Connected to Base44 platform: {API_BASE_URL}')
    
    # Initialize database connection
    db_connected = await init_database()
    if db_connected:
        print('✅ Database connected successfully')
        # Print database health info
        health = await db_manager.health_check()
        print(f'📊 Database status: {health["guild_count"]} guilds configured')
    else:
        print('⚠️ Database not connected - using default settings only')
    
    # Initialize guild settings for all servers
    for guild in discord_bot.guilds:
        print(f'  - {guild.name} (ID: {guild.id})')
        permissions = guild.me.guild_permissions
        print(f'    Permissions: Send Messages: {permissions.send_messages}, Manage Roles: {permissions.manage_roles}')
        
        # Initialize guild settings if database is connected
        if db_connected:
            settings = await get_guild_settings(str(guild.id))
            print(f'    Settings: Prefix="{settings["prefix"]}", Welcome="{settings["welcome_message"][:30]}..."')
    
    await affiliate_bot.log_bot_activity('startup', success=True)
    await affiliate_bot.update_bot_status({
        'status': 'active', 
        'message': 'Bot started successfully'
    }, affiliate_bot.config_id)
    asyncio.create_task(affiliate_bot.main_loop())

@discord_bot.event
async def on_member_join(member):
    """Handle new member joining the server."""
    try:
        guild_settings = await get_guild_settings(str(member.guild.id))
        
        # Send welcome message if configured
        welcome_message = guild_settings.get('welcome_message', 'Welcome to the server!')
        if welcome_message and welcome_message != 'Welcome to the server!':
            # Replace placeholders in welcome message
            formatted_message = welcome_message.replace('{username}', member.display_name)
            formatted_message = formatted_message.replace('{user_mention}', member.mention)
            formatted_message = formatted_message.replace('{server_name}', member.guild.name)
            
            # Try to send welcome message
            try:
                await member.send(formatted_message)
                await affiliate_bot.log_bot_activity('welcome_message_sent',
                    user_id=str(member.id),
                    guild_id=str(member.guild.id),
                    success=True
                )
            except discord.Forbidden:
                # User has DMs disabled, try to send in a general channel
                general_channel = member.guild.system_channel or member.guild.text_channels[0]
                if general_channel:
                    await general_channel.send(f"{member.mention} {formatted_message}")
                    await affiliate_bot.log_bot_activity('welcome_message_sent',
                        user_id=str(member.id),
                        guild_id=str(member.guild.id),
                        channel_type='public',
                        success=True
                    )
        
        # Assign roles on join if configured
        role_ids = guild_settings.get('roles_on_join', [])
        if role_ids:
            for role_id in role_ids:
                try:
                    role = member.guild.get_role(int(role_id))
                    if role:
                        await member.add_roles(role)
                        await affiliate_bot.log_bot_activity('auto_role_assigned',
                            user_id=str(member.id),
                            guild_id=str(member.guild.id),
                            role_name=role.name,
                            success=True
                        )
                except Exception as e:
                    await affiliate_bot.log_bot_activity('auto_role_failed',
                        user_id=str(member.id),
                        guild_id=str(member.guild.id),
                        role_id=role_id,
                        error_message=str(e),
                        success=False
                    )
        
    except Exception as e:
        print(f' Error handling member join: {e}')
        await affiliate_bot.log_bot_activity('member_join_error',
            user_id=str(member.id),
            guild_id=str(member.guild.id),
            error_message=str(e),
            success=False
        )

@discord_bot.event
async def on_member_update(before, after):
    try:
        if len(after.roles) > len(before.roles):
            new_roles = [role for role in after.roles if role not in before.roles]
            for role in new_roles:
                print(f' User {after.display_name} gained role: {role.name}')
                await affiliate_bot.log_bot_activity('user_targeted',
                    user_id=str(after.id),
                    role_targeted=role.name,
                    success=True
                )
    except Exception as e:
        print(f' Error handling member update: {e}')

@discord_bot.event
async def on_error(event, *args, **kwargs):
    print(f' Bot error in {event}: {args}')
    await affiliate_bot.log_bot_activity('error',
        error_message=f'Bot error in {event}: {args}',
        success=False
    )

# Guild Settings Management Commands
@discord_bot.command(name='prefix')
@commands.has_permissions(manage_guild=True)
async def set_prefix(ctx, new_prefix: str):
    """Set the bot's command prefix for this server."""
    if not new_prefix:
        await ctx.send("❌ Please provide a prefix!")
        return
    
    if len(new_prefix) > 5:
        await ctx.send("❌ Prefix must be 5 characters or less!")
        return
    
    success = await update_guild_settings(str(ctx.guild.id), {"prefix": new_prefix})
    if success:
        await ctx.send(f"✅ Prefix changed to `{new_prefix}`")
        await affiliate_bot.log_bot_activity('settings_changed',
            guild_id=str(ctx.guild.id),
            setting='prefix',
            new_value=new_prefix,
            success=True
        )
    else:
        await ctx.send("❌ Failed to update prefix. Using default settings.")

@discord_bot.command(name='settings')
@commands.has_permissions(manage_guild=True)
async def view_settings(ctx):
    """View current server settings."""
    settings = await get_guild_settings(str(ctx.guild.id))
    
    embed = discord.Embed(
        title=f"Settings for {ctx.guild.name}",
        color=discord.Color.blue()
    )
    embed.add_field(name="Command Prefix", value=f"`{settings['prefix']}`", inline=True)
    embed.add_field(name="Welcome Message", value=settings['welcome_message'][:50] + "..." if len(settings['welcome_message']) > 50 else settings['welcome_message'], inline=True)
    embed.add_field(name="Auto Roles", value=f"{len(settings['roles_on_join'])} roles" if settings['roles_on_join'] else "None", inline=True)
    embed.add_field(name="Auto Moderation", value="✅ Enabled" if settings.get('auto_moderation') else "❌ Disabled", inline=True)
    embed.add_field(name="Mod Log Channel", value=f"<#{settings['mod_log_channel']}>" if settings.get('mod_log_channel') else "Not set", inline=True)
    
    await ctx.send(embed=embed)

@discord_bot.command(name='welcome')
@commands.has_permissions(manage_guild=True)
async def set_welcome(ctx, *, message: str):
    """Set the welcome message for new members."""
    if not message:
        await ctx.send("❌ Please provide a welcome message!")
        return
    
    if len(message) > 500:
        await ctx.send("❌ Welcome message must be 500 characters or less!")
        return
    
    success = await update_guild_settings(str(ctx.guild.id), {"welcome_message": message})
    if success:
        await ctx.send(f"✅ Welcome message updated!")
        await affiliate_bot.log_bot_activity('settings_changed',
            guild_id=str(ctx.guild.id),
            setting='welcome_message',
            new_value=message[:100] + "..." if len(message) > 100 else message,
            success=True
        )
    else:
        await ctx.send("❌ Failed to update welcome message. Using default settings.")

@discord_bot.command(name='dbstatus')
@commands.has_permissions(manage_guild=True)
async def database_status(ctx):
    """Check database connection status."""
    health = await db_manager.health_check()
    
    embed = discord.Embed(
        title="Database Status",
        color=discord.Color.green() if health['connected'] else discord.Color.red()
    )
    embed.add_field(name="Connection", value="✅ Connected" if health['connected'] else "❌ Disconnected", inline=True)
    embed.add_field(name="Database", value=health['database_name'], inline=True)
    embed.add_field(name="Guilds Configured", value=str(health['guild_count']), inline=True)
    
    if health['error']:
        embed.add_field(name="Error", value=health['error'], inline=False)
    
    await ctx.send(embed=embed)

@discord_bot.command(name='sync')
@commands.has_permissions(manage_guild=True)
async def sync_with_dashboard(ctx):
    """Manually sync settings with Base44 dashboard."""
    try:
        # Get current Base44 config
        config = await affiliate_bot.get_bot_config()
        
        # Sync all settings including campaigns and target roles
        success = await db_manager.sync_from_base44(str(ctx.guild.id), config)
        
        if success:
            await ctx.send("✅ Successfully synced all settings with Base44 dashboard!")
            await ctx.send(f"📊 Synced: {len(config.get('message_templates', []))} templates, {len(config.get('target_roles', []))} target roles")
            await affiliate_bot.log_bot_activity('dashboard_sync',
                guild_id=str(ctx.guild.id),
                success=True
            )
        else:
            await ctx.send("❌ Failed to sync settings with dashboard.")
            
    except Exception as e:
        await ctx.send(f"❌ Error syncing with dashboard: {str(e)}")
        await affiliate_bot.log_bot_activity('dashboard_sync',
            guild_id=str(ctx.guild.id),
            error_message=str(e),
            success=False
        )

@discord_bot.command(name='campaigns')
@commands.has_permissions(manage_guild=True)
async def view_campaigns(ctx):
    """View current campaigns and target roles."""
    try:
        campaigns = await db_manager.get_campaigns(str(ctx.guild.id))
        target_roles = await db_manager.get_target_roles(str(ctx.guild.id))
        templates = await db_manager.get_message_templates(str(ctx.guild.id))
        
        embed = discord.Embed(
            title=f"Campaign Settings for {ctx.guild.name}",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Active Campaigns", value=str(len(campaigns)), inline=True)
        embed.add_field(name="Target Roles", value=str(len(target_roles)), inline=True)
        embed.add_field(name="Message Templates", value=str(len(templates)), inline=True)
        
        if target_roles:
            role_names = []
            for role_data in target_roles[:5]:  # Show first 5 roles
                role = ctx.guild.get_role(int(role_data.get('role_id', 0)))
                if role:
                    role_names.append(f"{role.name} {'✅' if role_data.get('enabled') else '❌'}")
            
            if role_names:
                embed.add_field(name="Target Roles", value="\n".join(role_names), inline=False)
        
        if templates:
            template_names = [t.get('name', 'Unnamed') for t in templates[:3]]
            embed.add_field(name="Templates", value="\n".join(template_names), inline=False)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error retrieving campaign data: {str(e)}")

@discord_bot.command(name='targetroles')
@commands.has_permissions(manage_guild=True)
async def view_target_roles(ctx):
    """View detailed target roles configuration."""
    try:
        target_roles = await db_manager.get_target_roles(str(ctx.guild.id))
        
        if not target_roles:
            await ctx.send("📋 No target roles configured yet. Use the Base44 dashboard to set them up.")
            return
        
        embed = discord.Embed(
            title=f"Target Roles for {ctx.guild.name}",
            color=discord.Color.blue()
        )
        
        for i, role_data in enumerate(target_roles, 1):
            role_id = role_data.get('role_id')
            role_name = role_data.get('role_name', 'Unknown Role')
            enabled = role_data.get('enabled', False)
            
            role = ctx.guild.get_role(int(role_id)) if role_id else None
            status = "✅ Active" if enabled else "❌ Disabled"
            role_mention = role.mention if role else f"<@&{role_id}>"
            
            embed.add_field(
                name=f"{i}. {role_name}",
                value=f"Role: {role_mention}\nStatus: {status}",
                inline=True
            )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error retrieving target roles: {str(e)}")

@discord_bot.command(name='status')
@commands.has_permissions(manage_guild=True)
async def bot_status(ctx):
    """Get comprehensive bot status including Base44 and database."""
    try:
        # Database status
        db_health = await db_manager.health_check()
        
        # Base44 status
        config = await affiliate_bot.get_bot_config()
        
        embed = discord.Embed(
            title="🤖 Bot Status Report",
            color=discord.Color.green() if db_health['connected'] else discord.Color.orange()
        )
        
        # Database status
        db_status = "✅ Connected" if db_health['connected'] else "❌ Disconnected"
        embed.add_field(name="Database", value=db_status, inline=True)
        embed.add_field(name="Guilds in DB", value=str(db_health['guild_count']), inline=True)
        
        # Base44 status
        base44_active = config.get('active', False)
        embed.add_field(name="Base44 Status", value="✅ Active" if base44_active else "❌ Inactive", inline=True)
        
        # Campaign stats
        templates_count = len(config.get('message_templates', []))
        target_roles_count = len(config.get('target_roles', []))
        affiliate_links_count = len(config.get('affiliate_links', []))
        
        embed.add_field(name="Message Templates", value=str(templates_count), inline=True)
        embed.add_field(name="Target Roles", value=str(target_roles_count), inline=True)
        embed.add_field(name="Affiliate Links", value=str(affiliate_links_count), inline=True)
        
        # Bot uptime and guild count
        embed.add_field(name="Servers", value=str(len(discord_bot.guilds)), inline=True)
        embed.add_field(name="Latency", value=f"{round(discord_bot.latency * 1000)}ms", inline=True)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error getting bot status: {str(e)}")

async def run_bot():
    try:
        await discord_bot.start(DISCORD_BOT_TOKEN)
    except Exception as e:
        print(f' Error starting bot: {e}')
        await affiliate_bot.log_bot_activity('shutdown', success=False)
    finally:
        await affiliate_bot.close()
        await close_database()  # Close database connection
        await discord_bot.close()

if __name__ == '__main__':
    print(' Starting Base44 Affiliate Bot...')
    print(f' Base44 Platform: {API_BASE_URL}')
    print(f' Bot ID: {BOT_ID}')
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print(' Bot stopped by user')
        asyncio.run(affiliate_bot.log_bot_activity('shutdown', success=True))
    except Exception as e:
        print(f' Fatal error: {e}')
        asyncio.run(affiliate_bot.log_bot_activity('shutdown', success=False))
