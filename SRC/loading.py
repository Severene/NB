"""
loading.py - Asset Loading and Management for Nanoverse Battery

This module handles loading, caching, and managing all game assets including
images, sounds, fonts, and other resources.
"""

import pygame
import os
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from config import *

class AssetType(Enum):
    IMAGE = "image"
    SOUND = "sound"
    FONT = "font"
    DATA = "data"
    SPRITESHEET = "spritesheet"

class LoadingState(Enum):
    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    LOADED = "loaded"
    FAILED = "failed"

class Asset:
    """Represents a single game asset"""
    
    def __init__(self, name: str, asset_type: AssetType, file_path: str, 
                 required: bool = False, fallback_path: str = None):
        self.name = name
        self.type = asset_type
        self.file_path = file_path
        self.required = required
        self.fallback_path = fallback_path
        self.state = LoadingState.NOT_LOADED
        self.data = None
        self.error_message = ""
        self.file_size = 0
        self.load_time = 0.0
        
        # Sprite sheet specific properties
        self.sprite_width = 16
        self.sprite_height = 16
        self.sprites_per_row = 1
        self.total_sprites = 1
        
    def set_spritesheet_properties(self, width: int, height: int, 
                                 sprites_per_row: int, total_sprites: int):
        """Set properties for sprite sheet assets"""
        self.sprite_width = width
        self.sprite_height = height
        self.sprites_per_row = sprites_per_row
        self.total_sprites = total_sprites

class AssetLoader:
    """Main asset loading and management system"""
    
    def __init__(self, assets_dir: str = "../assets"):
        self.assets_dir = assets_dir
        self.assets = {}  # Dict[str, Asset]
        self.loaded_data = {}  # Dict[str, Any] - actual pygame objects
        self.loading_progress = 0.0
        self.total_assets = 0
        self.loaded_assets = 0
        self.failed_assets = 0
        
        # Asset manifest - defines all game assets
        self.asset_manifest = {}
        
        # Cache settings
        self.cache_enabled = True
        self.max_cache_size = 100 * 1024 * 1024  # 100MB
        self.current_cache_size = 0
        
        # Loading callbacks
        self.progress_callback = None
        self.completion_callback = None
        
        self.initialize_asset_manifest()
        
    def initialize_asset_manifest(self):
        """Initialize the asset manifest with all game assets"""
        # Core UI and environment assets (all lowercase)
        self.register_asset("moon.png", AssetType.IMAGE, "moon.png", required=False)
        self.register_asset("sun.png", AssetType.IMAGE, "sun.png", required=False)
        self.register_asset("power.png", AssetType.IMAGE, "power.png", required=False)
        
        # Building assets (all lowercase)
        self.register_asset("tent.png", AssetType.IMAGE, "tent.png", required=False)
        self.register_asset("shack.png", AssetType.IMAGE, "shack.png", required=False)
        self.register_asset("small_home.png", AssetType.IMAGE, "small_home.png", required=False)
        self.register_asset("large_home.png", AssetType.IMAGE, "large_home.png", required=False)
        
        # Character sprite sheet (flexible sizing)
        nano_asset = self.register_asset("nanos.png", AssetType.SPRITESHEET, "nanos.png", required=True)
        if nano_asset:
            # We'll set the actual dimensions after loading
            nano_asset.set_spritesheet_properties(16, 16, 15, 80)  # Default values
            
        # Future assets (for expansion)
        self.register_asset("background_music.ogg", AssetType.SOUND, "background_music.ogg", required=False)
        self.register_asset("click_sound.wav", AssetType.SOUND, "click_sound.wav", required=False)
        self.register_asset("notification_sound.wav", AssetType.SOUND, "notification_sound.wav", required=False)
        
        # UI assets
        self.register_asset("button_click.wav", AssetType.SOUND, "button_click.wav", required=False)
        self.register_asset("error_sound.wav", AssetType.SOUND, "error_sound.wav", required=False)
        self.register_asset("success_sound.wav", AssetType.SOUND, "success_sound.wav", required=False)
        
        # Data files
        self.register_asset("nano_names.json", AssetType.DATA, "nano_names.json", required=False)
        self.register_asset("building_data.json", AssetType.DATA, "building_data.json", required=False)
        
        logging.info(f"Asset manifest initialized with {len(self.assets)} assets")
        
    def register_asset(self, name: str, asset_type: AssetType, file_path: str, 
                      required: bool = False, fallback_path: str = None) -> Optional[Asset]:
        """Register an asset in the manifest"""
        try:
            full_path = os.path.join(self.assets_dir, file_path)
            asset = Asset(name, asset_type, full_path, required, fallback_path)
            self.assets[name] = asset
            return asset
        except Exception as e:
            logging.error(f"Failed to register asset {name}: {str(e)}")
            return None
            
    def load_all_assets(self, progress_callback=None) -> bool:
        """Load all registered assets"""
        self.progress_callback = progress_callback
        self.total_assets = len(self.assets)
        self.loaded_assets = 0
        self.failed_assets = 0
        
        logging.info(f"Starting to load {self.total_assets} assets...")
        
        success = True
        for i, (name, asset) in enumerate(self.assets.items()):
            # Update progress
            self.loading_progress = i / self.total_assets if self.total_assets > 0 else 1.0
            if self.progress_callback:
                self.progress_callback(self.loading_progress, f"Loading {name}")
                
            # Load the asset
            if self.load_asset(name):
                self.loaded_assets += 1
            else:
                self.failed_assets += 1
                if asset.required:
                    logging.error(f"Required asset failed to load: {name}")
                    success = False
                    
        # Final progress update
        self.loading_progress = 1.0
        if self.progress_callback:
            self.progress_callback(1.0, "Loading complete")
            
        logging.info(f"Asset loading complete: {self.loaded_assets} loaded, {self.failed_assets} failed")
        return success
        
    def load_asset(self, name: str) -> bool:
        """Load a specific asset by name"""
        if name not in self.assets:
            logging.error(f"Asset not found in manifest: {name}")
            return False
            
        asset = self.assets[name]
        
        if asset.state == LoadingState.LOADED:
            return True  # Already loaded
            
        if asset.state == LoadingState.LOADING:
            logging.warning(f"Asset already being loaded: {name}")
            return False
            
        asset.state = LoadingState.LOADING
        
        try:
            import time
            start_time = time.time()
            
            # Check if file exists
            if not os.path.exists(asset.file_path):
                # Try fallback if available
                if asset.fallback_path and os.path.exists(asset.fallback_path):
                    asset.file_path = asset.fallback_path
                    logging.warning(f"Using fallback for {name}: {asset.fallback_path}")
                else:
                    raise FileNotFoundError(f"Asset file not found: {asset.file_path}")
                    
            # Get file size
            asset.file_size = os.path.getsize(asset.file_path)
            
            # Load based on asset type
            if asset.type == AssetType.IMAGE or asset.type == AssetType.SPRITESHEET:
                data = self.load_image(asset)
            elif asset.type == AssetType.SOUND:
                data = self.load_sound(asset)
            elif asset.type == AssetType.FONT:
                data = self.load_font(asset)
            elif asset.type == AssetType.DATA:
                data = self.load_data(asset)
            else:
                raise ValueError(f"Unknown asset type: {asset.type}")
                
            # Store loaded data
            self.loaded_data[name] = data
            asset.data = data
            asset.state = LoadingState.LOADED
            asset.load_time = time.time() - start_time
            
            # Update cache size
            self.current_cache_size += asset.file_size
            
            logging.debug(f"Loaded asset {name} ({asset.file_size} bytes, {asset.load_time:.3f}s)")
            return True
            
        except Exception as e:
            asset.state = LoadingState.FAILED
            asset.error_message = str(e)
            logging.error(f"Failed to load asset {name}: {str(e)}")
            return False
            
    def load_image(self, asset: Asset) -> pygame.Surface:
        """Load an image asset"""
        try:
            image = pygame.image.load(asset.file_path)
            
            # Convert for better performance
            if image.get_alpha() is not None:
                image = image.convert_alpha()
            else:
                image = image.convert()
                
            # Validate sprite sheet dimensions
            if asset.type == AssetType.SPRITESHEET:
                actual_width = image.get_width()
                actual_height = image.get_height()
                
                # Update sprite sheet properties based on actual dimensions
                if asset.name == "nanos.png":
                    # Auto-detect sprite sheet layout
                    asset.sprite_width = 16
                    asset.sprite_height = 16
                    asset.sprites_per_row = actual_width // 16
                    asset.total_sprites = (actual_width // 16) * (actual_height // 16)
                    
                    logging.info(f"Auto-detected sprite sheet: {actual_width}x{actual_height}, "
                               f"{asset.sprites_per_row}x{actual_height//16} sprites")
                else:
                    expected_width = asset.sprite_width * asset.sprites_per_row
                    expected_height = asset.sprite_height * (asset.total_sprites // asset.sprites_per_row)
                    
                    if actual_width != expected_width or actual_height != expected_height:
                        logging.warning(f"Sprite sheet {asset.name} dimensions don't match expected size: "
                                      f"expected {expected_width}x{expected_height}, "
                                      f"got {actual_width}x{actual_height}")
                    
            logging.debug(f"Loaded image {asset.name}: {image.get_width()}x{image.get_height()}")
            return image
            
        except Exception as e:
            raise Exception(f"Failed to load image: {str(e)}")
            
    def load_sound(self, asset: Asset) -> pygame.mixer.Sound:
        """Load a sound asset"""
        try:
            if not pygame.mixer.get_init():
                raise Exception("Audio system not initialized")
                
            sound = pygame.mixer.Sound(asset.file_path)
            logging.debug(f"Loaded sound {asset.name}: {sound.get_length():.2f}s")
            return sound
            
        except Exception as e:
            raise Exception(f"Failed to load sound: {str(e)}")
            
    def load_font(self, asset: Asset, size: int = 24) -> pygame.font.Font:
        """Load a font asset"""
        try:
            font = pygame.font.Font(asset.file_path, size)
            logging.debug(f"Loaded font {asset.name} at size {size}")
            return font
            
        except Exception as e:
            raise Exception(f"Failed to load font: {str(e)}")
            
    def load_data(self, asset: Asset) -> Any:
        """Load a data file (JSON, etc.)"""
        try:
            with open(asset.file_path, 'r', encoding='utf-8') as f:
                if asset.file_path.endswith('.json'):
                    data = json.load(f)
                else:
                    data = f.read()
                    
            logging.debug(f"Loaded data {asset.name}")
            return data
            
        except Exception as e:
            raise Exception(f"Failed to load data: {str(e)}")
            
    def get_asset(self, name: str) -> Any:
        """Get a loaded asset by name"""
        return self.loaded_data.get(name)
        
    def get_asset_info(self, name: str) -> Optional[Asset]:
        """Get asset information"""
        return self.assets.get(name)
        
    def is_loaded(self, name: str) -> bool:
        """Check if an asset is loaded"""
        asset = self.assets.get(name)
        return asset is not None and asset.state == LoadingState.LOADED
        
    def unload_asset(self, name: str) -> bool:
        """Unload an asset to free memory"""
        if name in self.loaded_data:
            asset = self.assets.get(name)
            if asset:
                self.current_cache_size -= asset.file_size
                asset.state = LoadingState.NOT_LOADED
                asset.data = None
                
            del self.loaded_data[name]
            logging.debug(f"Unloaded asset: {name}")
            return True
        return False
        
    def reload_asset(self, name: str) -> bool:
        """Reload an asset"""
        self.unload_asset(name)
        return self.load_asset(name)
        
    def get_sprite_from_sheet(self, sheet_name: str, sprite_index: int) -> Optional[pygame.Surface]:
        """Extract a single sprite from a sprite sheet"""
        if not self.is_loaded(sheet_name):
            return None
            
        asset = self.assets.get(sheet_name)
        if not asset or asset.type != AssetType.SPRITESHEET:
            return None
            
        sheet = self.get_asset(sheet_name)
        if not sheet:
            return None
            
        try:
            # Calculate sprite position
            row = sprite_index // asset.sprites_per_row
            col = sprite_index % asset.sprites_per_row
            
            x = col * asset.sprite_width
            y = row * asset.sprite_height
            
            # Extract sprite
            sprite_rect = pygame.Rect(x, y, asset.sprite_width, asset.sprite_height)
            sprite = sheet.subsurface(sprite_rect).copy()
            
            return sprite
            
        except Exception as e:
            logging.error(f"Failed to extract sprite {sprite_index} from {sheet_name}: {str(e)}")
            return None
            
    def get_sprite_animation(self, sheet_name: str, start_index: int, 
                           frame_count: int) -> List[pygame.Surface]:
        """Get a sequence of sprites for animation"""
        sprites = []
        for i in range(frame_count):
            sprite = self.get_sprite_from_sheet(sheet_name, start_index + i)
            if sprite:
                sprites.append(sprite)
            else:
                break
        return sprites
        
    def preload_common_assets(self) -> bool:
        """Preload commonly used assets"""
        common_assets = [
            "nanos.png",  # Always needed for Nanos
            "sun.png",    # UI elements
            "moon.png"
        ]
        
        success = True
        for asset_name in common_assets:
            if asset_name in self.assets:
                if not self.load_asset(asset_name):
                    success = False
                    
        return success
        
    def create_fallback_assets(self):
        """Create simple fallback assets if files are missing"""
        # Create a simple fallback nano sprite
        if not self.is_loaded("nanos.png"):
            try:
                # Create a 240x128 surface with simple colored squares
                fallback_sheet = pygame.Surface((240, 128), pygame.SRCALPHA)
                fallback_sheet.fill((0, 0, 0, 0))  # Transparent
                
                colors = [
                    (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255),
                    (0, 255, 255), (255, 255, 255), (255, 128, 0), (128, 0, 255), (255, 128, 128)
                ]
                
                # Create 10 different colored 16x16 sprites
                for i in range(10):
                    color = colors[i % len(colors)]
                    x = (i % 5) * 48  # 3 frames per character * 16 pixels
                    y = (i // 5) * 64  # 4 directions per character * 16 pixels
                    
                    # Draw simple colored rectangles for each animation frame
                    for frame in range(3):
                        for direction in range(4):
                            rect_x = x + frame * 16
                            rect_y = y + direction * 16
                            pygame.draw.rect(fallback_sheet, color, 
                                           (rect_x, rect_y, 16, 16))
                            pygame.draw.rect(fallback_sheet, (0, 0, 0), 
                                           (rect_x, rect_y, 16, 16), 1)
                            
                self.loaded_data["nanos.png"] = fallback_sheet
                if "nanos.png" in self.assets:
                    self.assets["nanos.png"].state = LoadingState.LOADED
                    self.assets["nanos.png"].data = fallback_sheet
                    
                logging.info("Created fallback nano sprite sheet")
                
            except Exception as e:
                logging.error(f"Failed to create fallback nano sprites: {str(e)}")
                
        # Create fallback sun and moon
        for asset_name, color in [("sun.png", (255, 255, 0)), ("moon.png", (200, 200, 200))]:
            if not self.is_loaded(asset_name):
                try:
                    fallback_surface = pygame.Surface((32, 32), pygame.SRCALPHA)
                    pygame.draw.circle(fallback_surface, color, (16, 16), 15)
                    pygame.draw.circle(fallback_surface, (0, 0, 0), (16, 16), 15, 2)
                    
                    self.loaded_data[asset_name] = fallback_surface
                    if asset_name in self.assets:
                        self.assets[asset_name].state = LoadingState.LOADED
                        self.assets[asset_name].data = fallback_surface
                        
                    logging.info(f"Created fallback {asset_name}")
                    
                except Exception as e:
                    logging.error(f"Failed to create fallback {asset_name}: {str(e)}")
                    
    def optimize_loaded_assets(self):
        """Optimize loaded assets for better performance"""
        for name, surface in self.loaded_data.items():
            if isinstance(surface, pygame.Surface):
                try:
                    # Convert to optimal format
                    if surface.get_alpha() is not None:
                        optimized = surface.convert_alpha()
                    else:
                        optimized = surface.convert()
                        
                    self.loaded_data[name] = optimized
                    
                except Exception as e:
                    logging.warning(f"Failed to optimize asset {name}: {str(e)}")
                    
    def get_loading_stats(self) -> Dict[str, Any]:
        """Get loading statistics"""
        return {
            'total_assets': self.total_assets,
            'loaded_assets': self.loaded_assets,
            'failed_assets': self.failed_assets,
            'cache_size': self.current_cache_size,
            'cache_size_mb': self.current_cache_size / (1024 * 1024),
            'loading_progress': self.loading_progress
        }
        
    def check_asset_integrity(self) -> Dict[str, bool]:
        """Check integrity of all loaded assets"""
        integrity_report = {}
        
        for name, asset in self.assets.items():
            if asset.state == LoadingState.LOADED:
                try:
                    # Basic checks
                    data = self.loaded_data.get(name)
                    integrity_report[name] = data is not None
                    
                    # Type-specific checks
                    if asset.type == AssetType.IMAGE and isinstance(data, pygame.Surface):
                        # Check if surface is valid
                        integrity_report[name] = data.get_width() > 0 and data.get_height() > 0
                        
                except Exception as e:
                    integrity_report[name] = False
                    logging.error(f"Asset integrity check failed for {name}: {str(e)}")
            else:
                integrity_report[name] = False
                
        return integrity_report
        
    def cleanup(self):
        """Clean up all loaded assets"""
        try:
            # Unload all assets
            for name in list(self.loaded_data.keys()):
                self.unload_asset(name)
                
            # Clear data structures
            self.loaded_data.clear()
            self.current_cache_size = 0
            self.loading_progress = 0.0
            
            logging.info("Asset loader cleanup completed")
            
        except Exception as e:
            logging.error(f"Error during asset loader cleanup: {str(e)}")

def create_asset_manifest_file(assets_dir: str = "assets", output_file: str = "asset_manifest.json"):
    """Create an asset manifest file by scanning the assets directory"""
    try:
        manifest = {
            "version": "1.0",
            "assets": {}
        }
        
        if os.path.exists(assets_dir):
            for filename in os.listdir(assets_dir):
                file_path = os.path.join(assets_dir, filename)
                if os.path.isfile(file_path):
                    # Determine asset type
                    ext = filename.lower().split('.')[-1]
                    if ext in ['png', 'jpg', 'jpeg', 'bmp', 'gif']:
                        asset_type = "image"
                    elif ext in ['wav', 'ogg', 'mp3']:
                        asset_type = "sound"
                    elif ext in ['ttf', 'otf']:
                        asset_type = "font"
                    elif ext in ['json', 'txt', 'xml']:
                        asset_type = "data"
                    else:
                        asset_type = "unknown"
                        
                    manifest["assets"][filename] = {
                        "type": asset_type,
                        "path": filename,
                        "required": filename in ["nanos.png"],  # Only critical assets required
                        "size": os.path.getsize(file_path)
                    }
                    
        with open(output_file, 'w') as f:
            json.dump(manifest, f, indent=2)
            
        logging.info(f"Created asset manifest: {output_file}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to create asset manifest: {str(e)}")
        return False

#EOF LOADING.PY # 598 lines
