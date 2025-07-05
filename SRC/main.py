"""
main.py - Main Game Loop and Entry Point for Nanoverse Battery

This is the main entry point for the Nanoverse Battery game. It handles the
initialization, main game loop, and cleanup.
"""

import sys
import os
import pygame
import traceback
import logging
import time
from typing import Optional, Dict, Any

# Import game modules (all in same directory)
from config import *
from boot import BootManager, quick_boot, debug_boot
from game import Game
from ui import UIRenderer
from environment import EnvironmentManager
from models import GameState
from loading import AssetLoader

class GameApplication:
    """Main game application class"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.running = False
        self.paused = False
        self.systems = {}
        
        # Core systems (initialized by boot)
        self.screen = None
        self.clock = None
        self.game = None
        self.ui_renderer = None
        self.environment_manager = None
        self.asset_loader = None
        self.game_state = None
        
        # Performance tracking
        self.fps = 0.0
        self.frame_count = 0
        self.last_fps_update = 0.0
        self.delta_time = 0.0
        
        # Game loop timing
        self.target_fps = TARGET_FPS
        self.max_frame_time = 1.0 / 30.0  # Cap at 30 FPS minimum
        self.accumulator = 0.0
        self.fixed_timestep = 1.0 / 60.0  # 60 Hz physics/logic updates
        
        # State management
        self.game_started = False
        self.boot_complete = False
        self.shutdown_requested = False
        
    def initialize(self) -> bool:
        """Initialize the game application"""
        try:
            logging.info("=== NANOVERSE BATTERY STARTING ===")
            logging.info(f"Game Version: {GAME_VERSION}")
            logging.info(f"Debug Mode: {self.debug_mode}")
            
            # Run boot sequence
            if self.debug_mode:
                success, systems = debug_boot()
            else:
                success, systems = quick_boot()
                
            if not success:
                logging.error("Boot sequence failed")
                return False
                
            # Store system references
            self.systems = systems
            self.screen = systems['screen']
            self.clock = systems['clock']
            self.game = systems['game']
            self.ui_renderer = systems['ui_renderer']
            self.environment_manager = systems['environment_manager']
            self.asset_loader = systems['asset_loader']
            self.game_state = systems['game_state']
            
            # IMPORTANT: Make sure game has access to assets
            if self.game and self.asset_loader:
                self.game.assets = self.asset_loader.loaded_data
                print(f"Game assets dictionary updated with {len(self.game.assets)} assets")
                print(f"Available assets: {list(self.game.assets.keys())}")
            
            self.boot_complete = True
            logging.info("Game initialization completed successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize game: {str(e)}")
            logging.error(traceback.format_exc())
            return False
            
    def run(self) -> int:
        """Main game loop - returns exit code"""
        if not self.initialize():
            return 1
            
        self.running = True
        self.game_started = True
        
        try:
            logging.info("Starting main game loop")
            
            # Show boot complete message briefly
            self.show_boot_complete_screen()
            
            # Main game loop
            while self.running:
                frame_start = time.time()
                
                # Calculate delta time
                self.delta_time = self.clock.tick(self.target_fps) / 1000.0
                self.delta_time = min(self.delta_time, self.max_frame_time)  # Cap frame time
                
                # Handle events
                self.handle_events()
                
                if not self.running:
                    break
                    
                # Update game state (fixed timestep)
                self.accumulator += self.delta_time
                while self.accumulator >= self.fixed_timestep:
                    if not self.paused:
                        self.update_game_state(self.fixed_timestep)
                    self.accumulator -= self.fixed_timestep
                    
                # Render frame
                self.render_frame()
                
                # Update performance tracking
                self.update_performance_tracking()
                
                # Handle any post-frame cleanup
                self.post_frame_cleanup()
                
            logging.info("Main game loop ended")
            return 0
            
        except KeyboardInterrupt:
            logging.info("Game interrupted by user")
            return 0
        except Exception as e:
            logging.error(f"Fatal error in main loop: {str(e)}")
            logging.error(traceback.format_exc())
            return 1
        finally:
            self.cleanup()
            
    def show_boot_complete_screen(self):
        """Show boot complete screen and wait for user input"""
        if not self.screen:
            return
            
        waiting = True
        start_time = time.time()
        
        while waiting and (time.time() - start_time) < 3.0:  # Max 3 seconds
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    waiting = False
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
                    
            # Render boot complete screen
            self.screen.fill(COLOR_BACKGROUND)
            
            # Create fonts
            font_large = pygame.font.Font(None, 48)
            font_medium = pygame.font.Font(None, 32)
            
            # Success message
            success_text = font_large.render("NANOVERSE BATTERY", True, COLOR_TEXT_ACCENT)
            success_rect = success_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
            self.screen.blit(success_text, success_rect)
            
            ready_text = font_medium.render("Ready to Begin!", True, COLOR_TEXT_SUCCESS)
            ready_rect = ready_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            self.screen.blit(ready_text, ready_rect)
            
            # Instructions
            instruction_text = font_medium.render("Click anywhere or press any key to start...", True, COLOR_TEXT_PRIMARY)
            instruction_rect = instruction_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
            self.screen.blit(instruction_text, instruction_rect)
            
            pygame.display.flip()
            self.clock.tick(60)
            
    def handle_events(self):
        """Handle all pygame events"""
        events = pygame.event.get()
        
        for event in events:
            if event.type == pygame.QUIT:
                self.request_shutdown()
                
            elif event.type == pygame.KEYDOWN:
                self.handle_key_down(event)
                
            elif event.type == pygame.KEYUP:
                self.handle_key_up(event)
                
            elif event.type == pygame.VIDEORESIZE:
                self.handle_window_resize(event.w, event.h)
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.debug_mode:
                    logging.debug(f"Mouse button {event.button} pressed at {event.pos}")
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                if self.debug_mode:
                    logging.debug(f"Mouse button {event.button} released at {event.pos}")
                    
        # Pass events to game system
        if self.game:
            # Store events for the game to process
            self.game.input_handler.update(events)
            
    def handle_key_down(self, event):
        """Handle key press events"""
        key = event.key
        
        # Global hotkeys
        if key == pygame.K_ESCAPE:
            self.request_shutdown()
        elif key == pygame.K_F11:
            self.toggle_fullscreen()
        elif key == pygame.K_PAUSE or key == pygame.K_SPACE:
            self.toggle_pause()
        elif key == pygame.K_F1 and self.debug_mode:
            self.toggle_debug_display()
        elif key == pygame.K_F5:
            self.quick_save()
        elif key == pygame.K_F9:
            self.quick_load()
            
        # Debug keys
        if self.debug_mode:
            if key == pygame.K_F2:
                self.debug_spawn_nano()
            elif key == pygame.K_F3:
                self.debug_add_resources()
            elif key == pygame.K_F4:
                self.debug_advance_time()
                
    def handle_key_up(self, event):
        """Handle key release events"""
        pass
        
    def handle_window_resize(self, width: int, height: int):
        """Handle window resize events"""
        try:
            # Update configuration
            update_display_config(width, height)
            
            # Recreate display surface
            self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
            
            # Update UI renderer
            if self.ui_renderer:
                self.ui_renderer.update_screen_size(width, height)
                
            # Update game
            if self.game:
                self.game.handle_resize(width, height)
                
            logging.info(f"Window resized to {width}x{height}")
            
        except Exception as e:
            logging.error(f"Failed to handle window resize: {str(e)}")
            
    def update_game_state(self, dt: float):
        """Update all game systems"""
        try:
            # Update environment first (affects everything else)
            if self.environment_manager:
                self.environment_manager.update(dt, WINDOW_WIDTH, WINDOW_HEIGHT)
                
            # Update main game logic
            if self.game:
                self.game.update(dt)
                
            # Apply environmental effects to game state
            if self.environment_manager and self.game_state:
                self.environment_manager.apply_environmental_effects(self.game_state, dt)
                
        except Exception as e:
            logging.error(f"Error updating game state: {str(e)}")
            if self.debug_mode:
                logging.error(traceback.format_exc())
                
    def render_frame(self):
        """Render the current frame"""
        try:
            if not self.screen or not self.ui_renderer:
                return
                
            # Clear screen
            self.screen.fill(COLOR_BACKGROUND)
            
            # Render main game UI
            if self.game and self.game_state:
                self.ui_renderer.render_all(self.game_state, self.game)
                
            # Render environmental effects
            if self.environment_manager:
                self.environment_manager.render_environmental_overlay(self.screen)
                
            # Render debug information
            if self.debug_mode:
                self.render_debug_info()
                
            # Render pause overlay
            if self.paused:
                self.render_pause_overlay()
                
            # Update display
            pygame.display.flip()
            
        except Exception as e:
            logging.error(f"Error rendering frame: {str(e)}")
            if self.debug_mode:
                logging.error(traceback.format_exc())
                
    def render_debug_info(self):
        """Render debug information overlay"""
        if not DEBUG_SHOW_FPS and not self.debug_mode:
            return
            
        try:
            font = pygame.font.Font(None, 24)
            y_offset = 10
            
            # FPS counter
            if DEBUG_SHOW_FPS:
                fps_text = font.render(f"FPS: {self.fps:.1f}", True, COLOR_DEBUG_TEXT)
                self.screen.blit(fps_text, (10, y_offset))
                y_offset += 25
                
            # Frame time
            frame_time_ms = self.delta_time * 1000
            frame_text = font.render(f"Frame: {frame_time_ms:.1f}ms", True, COLOR_DEBUG_TEXT)
            self.screen.blit(frame_text, (10, y_offset))
            y_offset += 25
            
            # Game state info
            if self.game_state:
                nanos_text = font.render(f"Nanos: {len(self.game_state.nanos)}", True, COLOR_DEBUG_TEXT)
                self.screen.blit(nanos_text, (10, y_offset))
                y_offset += 25
                
                eu_text = font.render(f"EU: {self.game_state.resources.surge_capacitor:.2f}", True, COLOR_DEBUG_TEXT)
                self.screen.blit(eu_text, (10, y_offset))
                y_offset += 25
                
            # Environment info
            if self.environment_manager:
                weather_text = font.render(f"Weather: {self.environment_manager.weather_system.current_weather.value}", 
                                         True, COLOR_DEBUG_TEXT)
                self.screen.blit(weather_text, (10, y_offset))
                y_offset += 25
                
                time_text = font.render(f"Time: {self.environment_manager.time_system.get_time_string()}", 
                                      True, COLOR_DEBUG_TEXT)
                self.screen.blit(time_text, (10, y_offset))
                
        except Exception as e:
            logging.error(f"Error rendering debug info: {str(e)}")
            
    def render_pause_overlay(self):
        """Render pause screen overlay"""
        try:
            # Semi-transparent overlay
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))
            
            # Pause text
            font = pygame.font.Font(None, 72)
            pause_text = font.render("PAUSED", True, COLOR_TEXT_PRIMARY)
            pause_rect = pause_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            self.screen.blit(pause_text, pause_rect)
            
            # Instructions
            font_small = pygame.font.Font(None, 32)
            instruction_text = font_small.render("Press SPACE to resume", True, COLOR_TEXT_SECONDARY)
            instruction_rect = instruction_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 60))
            self.screen.blit(instruction_text, instruction_rect)
            
        except Exception as e:
            logging.error(f"Error rendering pause overlay: {str(e)}")
            
    def update_performance_tracking(self):
        """Update FPS and performance metrics"""
        self.frame_count += 1
        current_time = time.time()
        
        if current_time - self.last_fps_update >= 1.0:  # Update every second
            self.fps = self.frame_count / (current_time - self.last_fps_update)
            self.frame_count = 0
            self.last_fps_update = current_time
            
    def post_frame_cleanup(self):
        """Perform any cleanup after frame rendering"""
        # Occasional garbage collection in debug mode
        if self.debug_mode and self.frame_count % (60 * 60) == 0:  # Every minute
            import gc
            gc.collect()
            
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        try:
            # This is a simple toggle - more sophisticated fullscreen handling could be added
            current_flags = self.screen.get_flags()
            if current_flags & pygame.FULLSCREEN:
                self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
                logging.info("Switched to windowed mode")
            else:
                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                logging.info("Switched to fullscreen mode")
                
        except Exception as e:
            logging.error(f"Failed to toggle fullscreen: {str(e)}")
            
    def toggle_pause(self):
        """Toggle game pause state"""
        self.paused = not self.paused
        logging.info(f"Game {'paused' if self.paused else 'resumed'}")
        
    def toggle_debug_display(self):
        """Toggle debug display options"""
        global DEBUG_SHOW_FPS, DEBUG_SHOW_GRID
        DEBUG_SHOW_FPS = not DEBUG_SHOW_FPS
        DEBUG_SHOW_GRID = not DEBUG_SHOW_GRID
        logging.info(f"Debug display toggled - FPS: {DEBUG_SHOW_FPS}, Grid: {DEBUG_SHOW_GRID}")
        
    def debug_spawn_nano(self):
        """Debug function to spawn a nano"""
        if self.game_state and self.debug_mode:
            nano = self.game_state.create_random_nano()
            if self.game_state.hire_nano(nano):
                logging.info(f"Debug: Spawned nano {nano.name}")
                
    def debug_add_resources(self):
        """Debug function to add resources"""
        if self.game_state and self.debug_mode:
            self.game_state.resources.credits += 1000
            self.game_state.resources.add_eu(50)
            logging.info("Debug: Added 1000 credits and 50 EU")
            
    def debug_advance_time(self):
        """Debug function to advance time"""
        if self.environment_manager and self.debug_mode:
            for _ in range(24):  # Advance 24 hours
                self.environment_manager.time_system.advance_hour()
            logging.info("Debug: Advanced time by 24 hours")
            
    def quick_save(self):
        """Quick save game state"""
        try:
            # Future: Implement save system
            logging.info("Quick save requested (not yet implemented)")
        except Exception as e:
            logging.error(f"Failed to quick save: {str(e)}")
            
    def quick_load(self):
        """Quick load game state"""
        try:
            # Future: Implement load system
            logging.info("Quick load requested (not yet implemented)")
        except Exception as e:
            logging.error(f"Failed to quick load: {str(e)}")
            
    def request_shutdown(self):
        """Request graceful shutdown"""
        logging.info("Shutdown requested")
        self.shutdown_requested = True
        self.running = False
        
    def cleanup(self):
        """Clean up resources and shutdown"""
        try:
            logging.info("Starting cleanup...")
            
            # Stop game systems
            if self.game:
                self.game.running = False
                
            # Cleanup asset loader
            if self.asset_loader:
                self.asset_loader.cleanup()
                
            # Cleanup pygame
            pygame.quit()
            
            logging.info("Cleanup completed successfully")
            
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")

def main():
    """Main entry point"""
    # Parse command line arguments
    debug_mode = "--debug" in sys.argv or "-d" in sys.argv
    
    # Create and run the game application
    app = GameApplication(debug_mode=debug_mode)
    exit_code = app.run()
    
    # Exit with appropriate code
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

#EOF main.py # 456 lines