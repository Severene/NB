"""
boot.py - Initialize Game Systems for Nanoverse Battery

This module handles the initialization of all game systems, loading assets,
setting up the game state, and preparing the game for launch.
"""

import pygame
import sys
import os
import logging
from typing import Dict, Any, Optional, Tuple
from config import *
from loading import AssetLoader
from models import GameState
from game import Game
from ui import UIRenderer
from environment import EnvironmentManager

class BootManager:
    """Manages the boot sequence and system initialization"""
    
    def __init__(self):
        self.boot_stage = 0
        self.boot_stages = [
            "Initializing Pygame",
            "Loading Configuration", 
            "Setting up Display",
            "Loading Assets",
            "Initializing Audio",
            "Creating Game State",
            "Setting up UI",
            "Initializing Environment",
            "Preparing Game Systems",
            "Final Setup"
        ]
        self.boot_progress = 0.0
        self.boot_complete = False
        self.error_occurred = False
        self.error_message = ""
        
        # Systems to initialize
        self.screen = None
        self.clock = None
        self.asset_loader = None
        self.game_state = None
        self.game = None
        self.ui_renderer = None
        self.environment_manager = None
        
        # Settings
        self.fullscreen = False
        self.vsync = True
        self.audio_enabled = True
        self.debug_mode = False
        
    def boot_game(self) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Main boot sequence - returns (success, systems_dict)
        Returns tuple of success status and dictionary of initialized systems
        """
        try:
            self.setup_logging()
            logging.info("=== NANOVERSE BATTERY BOOT SEQUENCE ===")
            
            # Stage 0: Initialize Pygame
            self.boot_stage = 0
            self.update_progress(0.0)
            if not self.initialize_pygame():
                return False, None
                
            # Stage 1: Load Configuration
            self.boot_stage = 1
            self.update_progress(0.1)
            if not self.load_configuration():
                return False, None
                
            # Stage 2: Set up Display
            self.boot_stage = 2
            self.update_progress(0.2)
            if not self.setup_display():
                return False, None
                
            # Stage 3: Load Assets
            self.boot_stage = 3
            self.update_progress(0.3)
            if not self.load_assets():
                return False, None
                
            # Stage 4: Initialize Audio
            self.boot_stage = 4
            self.update_progress(0.5)
            if not self.initialize_audio():
                return False, None
                
            # Stage 5: Create Game State
            self.boot_stage = 5
            self.update_progress(0.6)
            if not self.create_game_state():
                return False, None
                
            # Stage 6: Set up UI
            self.boot_stage = 6
            self.update_progress(0.7)
            if not self.setup_ui():
                return False, None
                
            # Stage 7: Initialize Environment
            self.boot_stage = 7
            self.update_progress(0.8)
            if not self.initialize_environment():
                return False, None
                
            # Stage 8: Prepare Game Systems
            self.boot_stage = 8
            self.update_progress(0.9)
            if not self.prepare_game_systems():
                return False, None
                
            # Stage 9: Final Setup
            self.boot_stage = 9
            self.update_progress(1.0)
            if not self.final_setup():
                return False, None
                
            self.boot_complete = True
            logging.info("Boot sequence completed successfully!")
            
            # Return all initialized systems
            systems = {
                'screen': self.screen,
                'clock': self.clock,
                'game': self.game,
                'ui_renderer': self.ui_renderer,
                'environment_manager': self.environment_manager,
                'asset_loader': self.asset_loader,
                'game_state': self.game_state
            }
            
            return True, systems
            
        except Exception as e:
            self.error_occurred = True
            self.error_message = f"Boot failed at stage {self.boot_stage}: {str(e)}"
            logging.error(self.error_message)
            return False, None
            
    def update_progress(self, progress: float):
        """Update boot progress and display"""
        self.boot_progress = progress
        stage_name = self.boot_stages[self.boot_stage] if self.boot_stage < len(self.boot_stages) else "Unknown"
        logging.info(f"Boot Stage {self.boot_stage}: {stage_name} ({progress*100:.1f}%)")
        
        # If screen is available, show boot screen
        if self.screen:
            self.render_boot_screen(stage_name, progress)
            
    def setup_logging(self):
        """Initialize logging system"""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        log_level = logging.DEBUG if self.debug_mode else logging.INFO
        
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Set up logging to file and console
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler('logs/nanoverse_boot.log', mode='w'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
    def initialize_pygame(self) -> bool:
        """Initialize Pygame and its subsystems"""
        try:
            # Initialize core Pygame
            pygame.init()
            logging.info("Pygame core initialized")
            
            # Initialize specific subsystems
            if not pygame.display.get_init():
                pygame.display.init()
                logging.info("Pygame display subsystem initialized")
                
            if not pygame.font.get_init():
                pygame.font.init()
                logging.info("Pygame font subsystem initialized")
                
            # Initialize clock
            self.clock = pygame.time.Clock()
            logging.info("Pygame clock initialized")
            
            # Check Pygame version
            pygame_version = pygame.version.ver
            logging.info(f"Pygame version: {pygame_version}")
            
            return True
            
        except Exception as e:
            self.error_message = f"Failed to initialize Pygame: {str(e)}"
            logging.error(self.error_message)
            return False
            
    def load_configuration(self) -> bool:
        """Load game configuration settings"""
        try:
            # Load settings from config file if it exists
            config_file = 'config/settings.ini'
            if os.path.exists(config_file):
                logging.info(f"Loading configuration from {config_file}")
                # Future: Load from INI file
                pass
            else:
                logging.info("Using default configuration")
                
            # Validate configuration values
            if WINDOW_WIDTH <= 0 or WINDOW_HEIGHT <= 0:
                raise ValueError("Invalid window dimensions in config")
                
            if GRID_SIZE <= 0:
                raise ValueError("Invalid grid size in config")
                
            logging.info(f"Configuration loaded - Window: {WINDOW_WIDTH}x{WINDOW_HEIGHT}, Grid: {GRID_SIZE}")
            return True
            
        except Exception as e:
            self.error_message = f"Failed to load configuration: {str(e)}"
            logging.error(self.error_message)
            return False
            
    def setup_display(self) -> bool:
        """Set up the display window"""
        try:
            # Set display mode
            flags = 0
            if self.fullscreen:
                flags |= pygame.FULLSCREEN
            if self.vsync:
                flags |= pygame.DOUBLEBUF
                
            self.screen = pygame.display.set_mode(
                (WINDOW_WIDTH, WINDOW_HEIGHT), 
                flags
            )
            
            # Set window properties
            pygame.display.set_caption(GAME_TITLE)
            
            # Try to set window icon if available
            icon_path = os.path.join('assets', 'icon.png')
            if os.path.exists(icon_path):
                try:
                    icon = pygame.image.load(icon_path)
                    pygame.display.set_icon(icon)
                    logging.info("Window icon set")
                except:
                    logging.warning("Could not load window icon")
                    
            # Allow window to be resizable
            if not self.fullscreen:
                # Future: pygame.RESIZABLE flag if needed
                pass
                
            logging.info(f"Display initialized: {WINDOW_WIDTH}x{WINDOW_HEIGHT}")
            logging.info(f"Display driver: {pygame.display.get_driver()}")
            
            return True
            
        except Exception as e:
            self.error_message = f"Failed to setup display: {str(e)}"
            logging.error(self.error_message)
            return False
            
    def load_assets(self) -> bool:
        """Load all game assets"""
        try:
            self.asset_loader = AssetLoader()
            
            # Define required assets (updated to lowercase)
            required_assets = [
                'moon.png',
                'sun.png', 
                'power.png',
                'tent.png',
                'shack.png',
                'small_home.png',
                'large_home.png',
                'nanos.png'
            ]
            
            # Load all assets
            success_count = 0
            total_assets = len(required_assets)
            
            for i, asset_name in enumerate(required_assets):
                try:
                    # Update progress for each asset
                    asset_progress = 0.3 + (i / total_assets) * 0.2  # Assets take 20% of boot time
                    self.update_progress(asset_progress)
                    
                    if self.asset_loader.load_asset(asset_name):
                        success_count += 1
                        logging.info(f"Loaded asset: {asset_name}")
                    else:
                        logging.warning(f"Failed to load asset: {asset_name}")
                        
                except Exception as e:
                    logging.warning(f"Error loading asset {asset_name}: {str(e)}")
                    
            # Check if critical assets loaded
            critical_assets = ['nanos.png']  # Assets required for basic functionality
            critical_loaded = all(self.asset_loader.get_asset(asset) is not None for asset in critical_assets)
            
            if not critical_loaded:
                logging.error("Critical assets missing - game may not function properly")
                
            logging.info(f"Assets loaded: {success_count}/{total_assets}")
            return True  # Continue even if some assets failed
            
        except Exception as e:
            self.error_message = f"Failed to load assets: {str(e)}"
            logging.error(self.error_message)
            return False
            
    def initialize_audio(self) -> bool:
        """Initialize audio system"""
        try:
            if self.audio_enabled:
                # Initialize pygame mixer
                pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
                pygame.mixer.init()
                
                # Test audio system
                if pygame.mixer.get_init():
                    logging.info("Audio system initialized successfully")
                    logging.info(f"Audio settings: {pygame.mixer.get_init()}")
                else:
                    logging.warning("Audio system failed to initialize")
                    self.audio_enabled = False
            else:
                logging.info("Audio disabled by configuration")
                
            return True
            
        except Exception as e:
            self.error_message = f"Failed to initialize audio: {str(e)}"
            logging.warning(self.error_message)
            self.audio_enabled = False
            return True  # Continue without audio
            
    def create_game_state(self) -> bool:
        """Create and initialize game state"""
        try:
            self.game_state = GameState()
            
            # Initialize with starting resources
            self.game_state.resources.credits = STARTING_CREDITS
            self.game_state.resources.eu = 0.0
            self.game_state.resources.work_power = STARTING_WORK_POWER
            
            # Generate initial hire candidates
            self.game_state.generate_hire_candidates()
            
            logging.info("Game state created successfully")
            logging.info(f"Starting credits: {STARTING_CREDITS}")
            logging.info(f"Starting work power: {STARTING_WORK_POWER}")
            
            return True
            
        except Exception as e:
            self.error_message = f"Failed to create game state: {str(e)}"
            logging.error(self.error_message)
            return False
            
    def setup_ui(self) -> bool:
        """Set up UI renderer"""
        try:
            if not self.screen:
                raise ValueError("Screen not initialized")
                
            self.ui_renderer = UIRenderer(self.screen)
            
            # Load UI-specific assets into renderer if needed
            if self.asset_loader:
                # Future: Pass specific UI assets to renderer
                pass
                
            logging.info("UI renderer initialized")
            return True
            
        except Exception as e:
            self.error_message = f"Failed to setup UI: {str(e)}"
            logging.error(self.error_message)
            return False
            
    def initialize_environment(self) -> bool:
        """Initialize environment manager"""
        try:
            self.environment_manager = EnvironmentManager()
            
            # Set initial environmental conditions
            # Could load from save file in future
            
            logging.info("Environment manager initialized")
            return True
            
        except Exception as e:
            self.error_message = f"Failed to initialize environment: {str(e)}"
            logging.error(self.error_message)
            return False
            
    def prepare_game_systems(self) -> bool:
        """Prepare main game systems"""
        try:
            if not all([self.screen, self.clock, self.game_state]):
                raise ValueError("Required systems not initialized")
                
            # Create main game instance
            self.game = Game(self.screen, self.clock)
            self.game.state = self.game_state
            
            # Pass assets to game
            if self.asset_loader:
                self.game.assets = self.asset_loader.assets
                
            # Set up system connections
            if self.ui_renderer:
                # Connect UI to game systems
                pass
                
            if self.environment_manager:
                # Connect environment to game
                pass
                
            logging.info("Game systems prepared")
            return True
            
        except Exception as e:
            self.error_message = f"Failed to prepare game systems: {str(e)}"
            logging.error(self.error_message)
            return False
            
    def final_setup(self) -> bool:
        """Final setup and validation"""
        try:
            # Validate all systems are ready
            required_systems = [
                ('screen', self.screen),
                ('clock', self.clock),
                ('game', self.game),
                ('ui_renderer', self.ui_renderer),
                ('environment_manager', self.environment_manager),
                ('game_state', self.game_state)
            ]
            
            for system_name, system in required_systems:
                if system is None:
                    raise ValueError(f"Required system not initialized: {system_name}")
                    
            # Perform initial render to test systems
            try:
                self.screen.fill((50, 50, 50))
                self.render_boot_complete()
                pygame.display.flip()
            except Exception as e:
                logging.warning(f"Initial render test failed: {str(e)}")
                
            # Run quick system tests
            self.run_system_tests()
            
            logging.info("Final setup completed successfully")
            return True
            
        except Exception as e:
            self.error_message = f"Failed final setup: {str(e)}"
            logging.error(self.error_message)
            return False
            
    def run_system_tests(self):
        """Run quick tests on initialized systems"""
        try:
            # Test game state
            if self.game_state:
                original_credits = self.game_state.resources.credits
                self.game_state.resources.spend_credits(1.0)
                if self.game_state.resources.credits == original_credits - 1.0:
                    logging.info("Game state test: PASS")
                else:
                    logging.warning("Game state test: FAIL")
                    
            # Test environment
            if self.environment_manager:
                original_hour = self.environment_manager.time_system.game_hour
                self.environment_manager.time_system.advance_hour()
                if self.environment_manager.time_system.game_hour != original_hour:
                    logging.info("Environment test: PASS")
                else:
                    logging.warning("Environment test: FAIL")
                    
        except Exception as e:
            logging.warning(f"System tests encountered error: {str(e)}")
            
    def render_boot_screen(self, stage_name: str, progress: float):
        """Render boot progress screen"""
        if not self.screen:
            return
            
        try:
            # Clear screen
            self.screen.fill((20, 20, 30))
            
            # Create fonts
            font_large = pygame.font.Font(None, 48)
            font_medium = pygame.font.Font(None, 32)
            font_small = pygame.font.Font(None, 24)
            
            # Draw title
            title_text = font_large.render("NANOVERSE BATTERY", True, (0, 255, 255))
            title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 100))
            self.screen.blit(title_text, title_rect)
            
            # Draw subtitle
            subtitle_text = font_medium.render("Initializing...", True, (255, 255, 255))
            subtitle_rect = subtitle_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 60))
            self.screen.blit(subtitle_text, subtitle_rect)
            
            # Draw stage name
            stage_text = font_small.render(stage_name, True, (200, 200, 200))
            stage_rect = stage_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20))
            self.screen.blit(stage_text, stage_rect)
            
            # Draw progress bar
            bar_width = 400
            bar_height = 20
            bar_x = (WINDOW_WIDTH - bar_width) // 2
            bar_y = WINDOW_HEIGHT // 2 + 20
            
            # Background
            pygame.draw.rect(self.screen, (60, 60, 60), 
                           (bar_x, bar_y, bar_width, bar_height))
            
            # Progress fill
            fill_width = int(bar_width * progress)
            pygame.draw.rect(self.screen, (0, 255, 255), 
                           (bar_x, bar_y, fill_width, bar_height))
            
            # Progress text
            progress_text = font_small.render(f"{progress * 100:.1f}%", True, (255, 255, 255))
            progress_rect = progress_text.get_rect(center=(WINDOW_WIDTH // 2, bar_y + bar_height + 30))
            self.screen.blit(progress_text, progress_rect)
            
            pygame.display.flip()
            
        except Exception as e:
            logging.warning(f"Failed to render boot screen: {str(e)}")
            
    def render_boot_complete(self):
        """Render boot completion screen"""
        if not self.screen:
            return
            
        try:
            self.screen.fill((20, 20, 30))
            
            font_large = pygame.font.Font(None, 48)
            font_medium = pygame.font.Font(None, 32)
            
            # Success message
            success_text = font_large.render("BOOT COMPLETE", True, (0, 255, 0))
            success_rect = success_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
            self.screen.blit(success_text, success_rect)
            
            # Instructions
            instruction_text = font_medium.render("Press any key to continue...", True, (255, 255, 255))
            instruction_rect = instruction_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
            self.screen.blit(instruction_text, instruction_rect)
            
        except Exception as e:
            logging.warning(f"Failed to render boot complete screen: {str(e)}")
            
    def render_boot_error(self):
        """Render boot error screen"""
        if not self.screen:
            return
            
        try:
            self.screen.fill((50, 20, 20))
            
            font_large = pygame.font.Font(None, 48)
            font_medium = pygame.font.Font(None, 24)
            
            # Error message
            error_text = font_large.render("BOOT FAILED", True, (255, 0, 0))
            error_rect = error_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
            self.screen.blit(error_text, error_rect)
            
            # Error details
            if self.error_message:
                lines = self.error_message.split('\n')
                for i, line in enumerate(lines[:3]):  # Show max 3 lines
                    detail_text = font_medium.render(line, True, (255, 255, 255))
                    detail_rect = detail_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + i * 25))
                    self.screen.blit(detail_text, detail_rect)
                    
            pygame.display.flip()
            
        except Exception as e:
            logging.error(f"Failed to render boot error screen: {str(e)}")
            
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.asset_loader:
                self.asset_loader.cleanup()
                
            pygame.quit()
            logging.info("Boot manager cleanup completed")
            
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")

def quick_boot() -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Quick boot function for easy game startup
    Returns (success, systems) tuple
    """
    boot_manager = BootManager()
    return boot_manager.boot_game()

def debug_boot() -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Debug boot with verbose logging
    Returns (success, systems) tuple
    """
    boot_manager = BootManager()
    boot_manager.debug_mode = True
    return boot_manager.boot_game()

#EOF BOOT.PY # 567 lines
