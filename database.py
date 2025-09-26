#!/usr/bin/env python3
"""
Database module for Discord bot with MongoDB integration.
Handles guild settings storage and retrieval with Base44 dashboard sync.
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages MongoDB connection and guild settings operations."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.mongo_uri = os.getenv('MONGO_URI')
        self.db_name = os.getenv('DB_NAME', 'discord_bot_db')
        self.is_connected = False
        
        # Default guild settings
        self.default_guild_settings = {
            "prefix": "!",
            "welcome_message": "Welcome to the server!",
            "roles_on_join": [],
            "mod_log_channel": None,
            "auto_moderation": False,
            "campaigns": [],
            "target_roles": [],
            "message_templates": [],
            "affiliate_links": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    
    async def connect(self) -> bool:
        """Establish connection to MongoDB."""
        if not self.mongo_uri:
            logger.warning("MONGO_URI not found in environment variables. Database features disabled.")
            return False
        
        try:
            self.client = AsyncIOMotorClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000,
                maxPoolSize=10
            )
            
            # Test connection
            await self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.is_connected = True
            
            logger.info(f"✅ Connected to MongoDB database: {self.db_name}")
            
            # Create indexes for better performance
            await self._create_indexes()
            
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            logger.warning("Bot will run with default settings only")
            self.is_connected = False
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected database error: {e}")
            self.is_connected = False
            return False
    
    async def _create_indexes(self):
        """Create database indexes for better performance."""
        try:
            guild_settings = self.db.guild_settings
            
            # Create index on guild_id for fast lookups
            await guild_settings.create_index("guild_id", unique=True)
            
            # Create index on updated_at for cleanup operations
            await guild_settings.create_index("updated_at")
            
            logger.info("✅ Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to create indexes: {e}")
    
    async def disconnect(self):
        """Close database connection."""
        if self.client:
            self.client.close()
            self.is_connected = False
            logger.info("🔌 Database connection closed")
    
    async def get_guild_settings(self, guild_id: str) -> Dict[str, Any]:
        """Get guild settings from database with fallback to defaults."""
        if not self.is_connected:
            logger.debug(f"Database not connected, using defaults for guild {guild_id}")
            return {**self.default_guild_settings, "guild_id": guild_id}
        
        try:
            guild_settings = self.db.guild_settings
            result = await guild_settings.find_one({"guild_id": str(guild_id)})
            
            if result:
                # Remove MongoDB's _id field from result
                result.pop('_id', None)
                logger.debug(f"✅ Retrieved settings for guild {guild_id}")
                return result
            else:
                logger.debug(f"⚠️ No settings found for guild {guild_id}, using defaults")
                return {**self.default_guild_settings, "guild_id": str(guild_id)}
                
        except Exception as e:
            logger.error(f"❌ Error getting guild settings for {guild_id}: {e}")
            return {**self.default_guild_settings, "guild_id": str(guild_id)}
    
    async def update_guild_settings(self, guild_id: str, settings: Dict[str, Any]) -> bool:
        """Update guild settings in database."""
        if not self.is_connected:
            logger.warning(f"Database not connected, cannot update settings for guild {guild_id}")
            return False
        
        try:
            guild_settings = self.db.guild_settings
            
            # Add metadata
            settings.update({
                "guild_id": str(guild_id),
                "updated_at": datetime.utcnow()
            })
            
            # Ensure created_at exists for new records
            if "created_at" not in settings:
                settings["created_at"] = datetime.utcnow()
            
            # Use upsert to create if doesn't exist, update if exists
            result = await guild_settings.update_one(
                {"guild_id": str(guild_id)},
                {"$set": settings},
                upsert=True
            )
            
            logger.info(f"✅ Updated settings for guild {guild_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating guild settings for {guild_id}: {e}")
            return False
    
    async def get_prefix(self, guild_id: str) -> str:
        """Get the command prefix for a specific guild."""
        settings = await self.get_guild_settings(guild_id)
        return settings.get("prefix", "!")
    
    async def set_prefix(self, guild_id: str, prefix: str) -> bool:
        """Set the command prefix for a specific guild."""
        return await self.update_guild_settings(guild_id, {"prefix": prefix})
    
    async def get_welcome_message(self, guild_id: str) -> str:
        """Get the welcome message for a specific guild."""
        settings = await self.get_guild_settings(guild_id)
        return settings.get("welcome_message", "Welcome to the server!")
    
    async def set_welcome_message(self, guild_id: str, message: str) -> bool:
        """Set the welcome message for a specific guild."""
        return await self.update_guild_settings(guild_id, {"welcome_message": message})
    
    async def get_roles_on_join(self, guild_id: str) -> List[str]:
        """Get the roles to assign on join for a specific guild."""
        settings = await self.get_guild_settings(guild_id)
        return settings.get("roles_on_join", [])
    
    async def set_roles_on_join(self, guild_id: str, role_ids: List[str]) -> bool:
        """Set the roles to assign on join for a specific guild."""
        return await self.update_guild_settings(guild_id, {"roles_on_join": role_ids})
    
    async def get_all_guilds(self) -> List[Dict[str, Any]]:
        """Get all guild settings from database."""
        if not self.is_connected:
            logger.warning("Database not connected, cannot retrieve all guilds")
            return []
        
        try:
            guild_settings = self.db.guild_settings
            cursor = guild_settings.find({})
            results = []
            
            async for document in cursor:
                document.pop('_id', None)
                results.append(document)
            
            logger.info(f"✅ Retrieved {len(results)} guild settings")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error getting all guild settings: {e}")
            return []
    
    async def delete_guild_settings(self, guild_id: str) -> bool:
        """Delete guild settings from database."""
        if not self.is_connected:
            logger.warning(f"Database not connected, cannot delete settings for guild {guild_id}")
            return False
        
        try:
            guild_settings = self.db.guild_settings
            result = await guild_settings.delete_one({"guild_id": str(guild_id)})
            
            if result.deleted_count > 0:
                logger.info(f"✅ Deleted settings for guild {guild_id}")
                return True
            else:
                logger.warning(f"⚠️ No settings found to delete for guild {guild_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error deleting guild settings for {guild_id}: {e}")
            return False
    
    async def get_campaigns(self, guild_id: str) -> List[Dict[str, Any]]:
        """Get campaigns for a specific guild."""
        settings = await self.get_guild_settings(guild_id)
        return settings.get("campaigns", [])
    
    async def set_campaigns(self, guild_id: str, campaigns: List[Dict[str, Any]]) -> bool:
        """Set campaigns for a specific guild."""
        return await self.update_guild_settings(guild_id, {"campaigns": campaigns})
    
    async def get_target_roles(self, guild_id: str) -> List[Dict[str, Any]]:
        """Get target roles for a specific guild."""
        settings = await self.get_guild_settings(guild_id)
        return settings.get("target_roles", [])
    
    async def set_target_roles(self, guild_id: str, target_roles: List[Dict[str, Any]]) -> bool:
        """Set target roles for a specific guild."""
        return await self.update_guild_settings(guild_id, {"target_roles": target_roles})
    
    async def get_message_templates(self, guild_id: str) -> List[Dict[str, Any]]:
        """Get message templates for a specific guild."""
        settings = await self.get_guild_settings(guild_id)
        return settings.get("message_templates", [])
    
    async def set_message_templates(self, guild_id: str, templates: List[Dict[str, Any]]) -> bool:
        """Set message templates for a specific guild."""
        return await self.update_guild_settings(guild_id, {"message_templates": templates})
    
    async def get_affiliate_links(self, guild_id: str) -> List[Dict[str, Any]]:
        """Get affiliate links for a specific guild."""
        settings = await self.get_guild_settings(guild_id)
        return settings.get("affiliate_links", [])
    
    async def set_affiliate_links(self, guild_id: str, links: List[Dict[str, Any]]) -> bool:
        """Set affiliate links for a specific guild."""
        return await self.update_guild_settings(guild_id, {"affiliate_links": links})
    
    async def sync_from_base44(self, guild_id: str, base44_config: Dict[str, Any]) -> bool:
        """Sync guild settings from Base44 dashboard configuration."""
        if not base44_config:
            return False
        
        try:
            # Extract settings from Base44 config
            sync_settings = {
                "campaigns": base44_config.get("campaigns", []),
                "target_roles": base44_config.get("target_roles", []),
                "message_templates": base44_config.get("message_templates", []),
                "affiliate_links": base44_config.get("affiliate_links", []),
                "prefix": base44_config.get("prefix", "!"),
                "welcome_message": base44_config.get("welcome_message", "Welcome to the server!"),
                "auto_moderation": base44_config.get("auto_moderation", False)
            }
            
            success = await self.update_guild_settings(guild_id, sync_settings)
            if success:
                logger.info(f"✅ Synced Base44 config for guild {guild_id}")
            return success
            
        except Exception as e:
            logger.error(f"❌ Error syncing Base44 config for guild {guild_id}: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health and return status information."""
        health_info = {
            "connected": self.is_connected,
            "database_name": self.db_name,
            "guild_count": 0,
            "error": None
        }
        
        if not self.is_connected:
            health_info["error"] = "Not connected to database"
            return health_info
        
        try:
            # Test connection
            await self.client.admin.command('ping')
            
            # Get guild count
            guild_settings = self.db.guild_settings
            health_info["guild_count"] = await guild_settings.count_documents({})
            
            logger.info(f"✅ Database health check passed: {health_info['guild_count']} guilds")
            
        except Exception as e:
            health_info["error"] = str(e)
            logger.error(f"❌ Database health check failed: {e}")
        
        return health_info

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions for easy access
async def get_prefix(bot, message) -> str:
    """Get command prefix for a guild. Used by discord.py for dynamic prefixes."""
    guild_id = str(message.guild.id) if message.guild else "0"
    return await db_manager.get_prefix(guild_id)

async def get_guild_settings(guild_id: str) -> Dict[str, Any]:
    """Get guild settings from database."""
    return await db_manager.get_guild_settings(guild_id)

async def update_guild_settings(guild_id: str, settings: Dict[str, Any]) -> bool:
    """Update guild settings in database."""
    return await db_manager.update_guild_settings(guild_id, settings)

async def init_database() -> bool:
    """Initialize database connection."""
    return await db_manager.connect()

async def close_database():
    """Close database connection."""
    await db_manager.disconnect()
