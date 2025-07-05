"""
ui.py - User Interface Elements and Rendering for Nanoverse Battery

This module handles all UI rendering including buttons, panels, text, and visual elements.
"""

import pygame
import math
from typing import List, Dict, Optional, Tuple
from enum import Enum
from models import *
from config import *

class GameMode(Enum):
    NORMAL = "normal"
    BUILD_CELL = "build_cell"
    BUILD_BUILDING = "build_building"
    MOVE_NANO = "move_nano"

class UIRenderer:
    """Handles all UI rendering for the game"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        
        # Initialize fonts
        pygame.font.init()
        self.font_small = pygame.font.Font(None, 16)
        self.font_medium = pygame.font.Font(None, 20)
        self.font_large = pygame.font.Font(None, 24)
        self.font_title = pygame.font.Font(None, 32)
        
        # Colors
        self.bg_color = (50, 50, 50)  # Dark grey background
        self.panel_color = (70, 70, 70)
        self.button_color = (100, 100, 100)
        self.button_hover_color = (120, 120, 120)
        self.button_pressed_color = (80, 80, 80)
        self.text_color = (255, 255, 255)
        self.accent_color = (0, 255, 255)  # Cyan
        self.warning_color = (255, 255, 0)  # Yellow
        self.error_color = (255, 0, 0)  # Red
        self.success_color = (0, 255, 0)  # Green
        self.play_area_color = (0, 100, 0)  # Green
        self.fence_color = (139, 69, 19)  # Brown
        self.center_square_color = (0, 0, 255)  # Blue
        self.grid_color = (0, 80, 0)  # Dark green
        
        # Cache for rendered text
        self.text_cache = {}
        
    def update_screen_size(self, width: int, height: int):
        """Update screen dimensions"""
        self.screen_width = width
        self.screen_height = height
        
    def render_all(self, game_state: GameState, game):
        """Render the entire game UI"""
        try:
            print("Starting render_all...")
            
            # Clear screen
            self.screen.fill(self.bg_color)
            print("Screen cleared")
            
            # Render main components
            self.render_time_bar(game_state, game)
            print("Time bar rendered")
            
            self.render_play_area(game_state, game)
            print("Play area rendered")
            
            self.render_left_panel(game_state, game)
            print("Left panel rendered")
            
            self.render_right_panel(game_state, game)
            print("Right panel rendered")
            
            self.render_bottom_status_lcd(game_state)
            print("Bottom status rendered")
            
            self.render_floating_labels(game.floating_labels)
            self.render_power_effects(game.power_effects, game)
            
            # Only render debris if the attribute exists
            if hasattr(game, 'debris_objects'):
                self.render_debris(game.debris_objects, game)
                print("Debris rendered")
            
            # Add day/night overlay
            self.render_day_night_overlay(game_state)
            print("Day/night overlay rendered")
            
            print("render_all completed successfully")
            
        except Exception as e:
            print(f"Error rendering UI: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: at least clear the screen
            self.screen.fill(self.bg_color)
        
    def render_time_bar(self, game_state: GameState, game):
        """Render the time bar with sun/moon and weather"""
        # Time bar background
        time_rect = pygame.Rect(0, 0, self.screen_width, TIME_BAR_HEIGHT)
        pygame.draw.rect(self.screen, (30, 30, 60), time_rect)
        
        # Sky gradient based on time
        is_day = game_state.is_daytime()
        if is_day:
            # Day colors - brighter
            sky_color = (135, 206, 235)  # Sky blue
            sun_moon_color = (255, 255, 0)  # Yellow sun
            symbol = "☀"
        else:
            # Night colors - much darker
            sky_color = (25, 25, 80)  # Dark night blue
            sun_moon_color = (200, 200, 200)  # White moon
            symbol = "🌙"
            
        # Draw sky gradient
        for y in range(TIME_BAR_HEIGHT):
            blend = y / TIME_BAR_HEIGHT
            if is_day:
                color = (
                    int(sky_color[0] * (1 - blend) + self.bg_color[0] * blend),
                    int(sky_color[1] * (1 - blend) + self.bg_color[1] * blend),
                    int(sky_color[2] * (1 - blend) + self.bg_color[2] * blend)
                )
            else:
                # Night - darker blend
                color = (
                    int(sky_color[0] * (1 - blend) + 20 * blend),
                    int(sky_color[1] * (1 - blend) + 20 * blend),
                    int(sky_color[2] * (1 - blend) + 40 * blend)
                )
            pygame.draw.line(self.screen, color, (0, y), (self.screen_width, y))
            
        # Draw sun/moon position with smooth movement
        sun_pos = game_state.get_sun_moon_position()
        sun_x = int(sun_pos * (self.screen_width - 60)) + 30
        sun_y = TIME_BAR_HEIGHT // 2
        
        # Draw sun/moon circle
        pygame.draw.circle(self.screen, sun_moon_color, (sun_x, sun_y), 15)
        
        # Draw time text with minutes for smooth progression
        time_text = f"Day {game_state.game_day + 1} - {game_state.game_hour:02d}:{game_state.game_minute:02d}"
        self.draw_text(time_text, self.font_medium, self.text_color, 10, 5)
        
        # Draw weather info - get from environment manager if available
        weather_text = "Clear"  # Default
        if hasattr(game, 'environment_manager') and game.environment_manager:
            current_weather = game.environment_manager.weather_system.current_weather.value
            weather_text = current_weather.title()  # Capitalize first letter
            
        self.draw_text(weather_text, self.font_small, self.text_color, 10, 25)
        
    def render_play_area(self, game_state: GameState, game):
        """Render the main play area"""
        # Calculate play area position
        play_rect = pygame.Rect(
            UI_PANEL_WIDTH + 10,
            TIME_BAR_HEIGHT + 10,
            self.screen_width - UI_PANEL_WIDTH - INFO_PANEL_WIDTH - 30,
            self.screen_height - TIME_BAR_HEIGHT - 100
        )
        
        # Fill play area background
        pygame.draw.rect(self.screen, self.play_area_color, play_rect)
        
        # Draw grid lines (lighter color for future roads)
        grid_color = (0, 120, 0)  # Lighter green for grid lines
        
        # Calculate exact grid dimensions to fill play area perfectly
        grid_cols = play_rect.width // GRID_SIZE
        grid_rows = play_rect.height // GRID_SIZE
        
        # Adjust play area to be exactly grid-aligned
        aligned_width = grid_cols * GRID_SIZE
        aligned_height = grid_rows * GRID_SIZE
        
        # Center the aligned play area
        offset_x = (play_rect.width - aligned_width) // 2
        offset_y = (play_rect.height - aligned_height) // 2
        
        aligned_rect = pygame.Rect(
            play_rect.x + offset_x, 
            play_rect.y + offset_y, 
            aligned_width, 
            aligned_height
        )
        
        # Draw aligned background
        pygame.draw.rect(self.screen, self.play_area_color, aligned_rect)
        
        # Draw vertical grid lines
        for x in range(grid_cols + 1):
            line_x = aligned_rect.x + x * GRID_SIZE
            pygame.draw.line(self.screen, grid_color, 
                           (line_x, aligned_rect.y), 
                           (line_x, aligned_rect.y + aligned_height), 1)
            
        # Draw horizontal grid lines  
        for y in range(grid_rows + 1):
            line_y = aligned_rect.y + y * GRID_SIZE
            pygame.draw.line(self.screen, grid_color, 
                           (aligned_rect.x, line_y), 
                           (aligned_rect.x + aligned_width, line_y), 1)
            
        # Draw fence around aligned play area
        pygame.draw.rect(self.screen, self.fence_color, aligned_rect, 3)
        
        # Draw center focal point - make it more interesting than just blue square
        center_grid_x = grid_cols // 2
        center_grid_y = grid_rows // 2
        center_x = aligned_rect.x + center_grid_x * GRID_SIZE
        center_y = aligned_rect.y + center_grid_y * GRID_SIZE
        
        # Create an interesting central hub - like a power core
        hub_rect = pygame.Rect(center_x, center_y, GRID_SIZE, GRID_SIZE)
        
        # Draw a glowing power core effect
        # Outer glow
        pygame.draw.rect(self.screen, (0, 50, 150), hub_rect.inflate(4, 4))
        # Inner core
        pygame.draw.rect(self.screen, (0, 100, 255), hub_rect)
        # Central bright spot
        center_point = hub_rect.center
        pygame.draw.circle(self.screen, (150, 200, 255), center_point, 8)
        pygame.draw.circle(self.screen, (255, 255, 255), center_point, 4)
        
        # Add some energy lines radiating out
        for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
            import math
            radians = math.radians(angle)
            end_x = center_point[0] + math.cos(radians) * 12
            end_y = center_point[1] + math.sin(radians) * 12
            pygame.draw.line(self.screen, (100, 150, 255), center_point, (int(end_x), int(end_y)), 2)
        
        # Store aligned rect for other rendering functions
        self.current_play_rect = aligned_rect
        
        # Draw buildings
        self.render_buildings(game_state, aligned_rect)
        
        # Draw cells
        self.render_cells(game_state, aligned_rect)
        
        # Draw Nanos
        nano_asset = game.assets.get('nanos.png')  # Get from game.assets dict
        self.render_nanos(game_state, aligned_rect, nano_asset)
        
        # Draw build preview if in build mode
        if hasattr(game, 'mode'):
            if game.mode == GameMode.BUILD_CELL or game.mode == GameMode.BUILD_BUILDING:
                self.render_build_preview(game, aligned_rect)
                
    def render_buildings(self, game_state: GameState, play_rect: pygame.Rect):
        """Render all buildings in the play area with better graphics"""
        for building in game_state.buildings.values():
            x = play_rect.x + building.x * GRID_SIZE
            y = play_rect.y + building.y * GRID_SIZE
            building_rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
            
            # Building colors based on type
            colors = {
                BuildingType.BIO: (0, 255, 0),     # Green
                BuildingType.TENT: (139, 69, 19),  # Brown
                BuildingType.STUDY: (0, 0, 255),   # Blue
                BuildingType.MUSIC: (255, 20, 147), # Pink
                BuildingType.CAMP: (128, 128, 128)  # Gray
            }
            
            color = colors.get(building.type, (100, 100, 100))
            
            # Draw different shapes for different building types
            if building.type == BuildingType.BIO:
                # BIO: Circle (generator)
                pygame.draw.circle(self.screen, color, building_rect.center, GRID_SIZE // 2 - 2)
                pygame.draw.circle(self.screen, (0, 0, 0), building_rect.center, GRID_SIZE // 2 - 2, 2)
                # Add energy symbol
                pygame.draw.circle(self.screen, (255, 255, 255), building_rect.center, 4)
                
            elif building.type == BuildingType.TENT:
                # TENT: Triangle (home)
                points = [
                    (building_rect.centerx, building_rect.top + 4),
                    (building_rect.left + 4, building_rect.bottom - 4),
                    (building_rect.right - 4, building_rect.bottom - 4)
                ]
                pygame.draw.polygon(self.screen, color, points)
                pygame.draw.polygon(self.screen, (0, 0, 0), points, 2)
                
            elif building.type == BuildingType.STUDY:
                # STUDY: Rectangle with roof (school)
                main_rect = pygame.Rect(x + 4, y + 8, GRID_SIZE - 8, GRID_SIZE - 12)
                pygame.draw.rect(self.screen, color, main_rect)
                pygame.draw.rect(self.screen, (0, 0, 0), main_rect, 2)
                # Roof triangle
                roof_points = [
                    (building_rect.centerx, y + 2),
                    (x + 2, y + 10),
                    (x + GRID_SIZE - 2, y + 10)
                ]
                pygame.draw.polygon(self.screen, (100, 0, 0), roof_points)
                pygame.draw.polygon(self.screen, (0, 0, 0), roof_points, 1)
                
            elif building.type == BuildingType.MUSIC:
                # MUSIC: Star shape (entertainment)
                center_x, center_y = building_rect.center
                outer_radius = GRID_SIZE // 2 - 3
                inner_radius = outer_radius // 2
                points = []
                for i in range(10):  # 5-pointed star
                    angle = i * 3.14159 / 5
                    if i % 2 == 0:
                        # Outer point
                        px = center_x + outer_radius * math.cos(angle - 3.14159/2)
                        py = center_y + outer_radius * math.sin(angle - 3.14159/2)
                    else:
                        # Inner point
                        px = center_x + inner_radius * math.cos(angle - 3.14159/2)
                        py = center_y + inner_radius * math.sin(angle - 3.14159/2)
                    points.append((px, py))
                pygame.draw.polygon(self.screen, color, points)
                pygame.draw.polygon(self.screen, (0, 0, 0), points, 2)
                
            elif building.type == BuildingType.CAMP:
                # CAMP: Hexagon (military)
                center_x, center_y = building_rect.center
                radius = GRID_SIZE // 2 - 3
                points = []
                for i in range(6):
                    angle = i * 3.14159 / 3
                    px = center_x + radius * math.cos(angle)
                    py = center_y + radius * math.sin(angle)
                    points.append((px, py))
                pygame.draw.polygon(self.screen, color, points)
                pygame.draw.polygon(self.screen, (0, 0, 0), points, 2)
                
            else:
                # Default: Square
                pygame.draw.rect(self.screen, color, building_rect)
                pygame.draw.rect(self.screen, (0, 0, 0), building_rect, 2)
            
            # Draw building letter on white background for visibility
            letters = {
                BuildingType.BIO: "B",
                BuildingType.TENT: "T", 
                BuildingType.STUDY: "S",
                BuildingType.MUSIC: "M",
                BuildingType.CAMP: "C"
            }
            
            letter = letters.get(building.type, "?")
            text_surface = self.font_medium.render(letter, True, (0, 0, 0))
            text_rect = text_surface.get_rect()
            text_rect.center = building_rect.center
            
            # White background circle for letter
            pygame.draw.circle(self.screen, (255, 255, 255), text_rect.center, 8)
            pygame.draw.circle(self.screen, (0, 0, 0), text_rect.center, 8, 1)
            self.screen.blit(text_surface, text_rect)
            
            # Show worker count at bottom
            worker_count = len(building.workers)
            count_text = f"{worker_count}/{building.capacity}"
            count_surface = self.font_small.render(count_text, True, (0, 0, 0))
            count_rect = count_surface.get_rect()
            count_rect.centerx = building_rect.centerx
            count_rect.bottom = building_rect.bottom - 2
            
            # White background for count
            count_bg = count_rect.inflate(4, 2)
            pygame.draw.rect(self.screen, (255, 255, 255), count_bg)
            pygame.draw.rect(self.screen, (0, 0, 0), count_bg, 1)
            self.screen.blit(count_surface, count_rect)
            
    def render_cells(self, game_state: GameState, play_rect: pygame.Rect):
        """Render all power cells as hexagons"""
        for cell in game_state.cells.values():
            x = play_rect.x + cell.x * GRID_SIZE
            y = play_rect.y + cell.y * GRID_SIZE
            center_x = x + GRID_SIZE // 2
            center_y = y + GRID_SIZE // 2
            
            # Cell color based on activity
            if cell.active:
                cell_color = (255, 255, 0)  # Yellow when active
                inner_color = (255, 255, 150)  # Lighter inner
            else:
                cell_color = (128, 128, 0)  # Dim when inactive
                inner_color = (200, 200, 100)  # Dim inner
            
            # Draw hexagonal cell
            radius = GRID_SIZE // 2 - 4
            points = []
            for i in range(6):
                angle = i * 3.14159 / 3
                px = center_x + radius * math.cos(angle)
                py = center_y + radius * math.sin(angle)
                points.append((px, py))
            
            # Draw filled hexagon
            pygame.draw.polygon(self.screen, cell_color, points)
            pygame.draw.polygon(self.screen, (0, 0, 0), points, 2)
            
            # Draw inner hexagon for 3D effect
            inner_radius = radius - 3
            inner_points = []
            for i in range(6):
                angle = i * 3.14159 / 3
                px = center_x + inner_radius * math.cos(angle)
                py = center_y + inner_radius * math.sin(angle)
                inner_points.append((px, py))
            pygame.draw.polygon(self.screen, inner_color, inner_points)
            
            # Draw cell number at top
            number_text = f"#{cell.cell_number}"
            number_surface = self.font_small.render(number_text, True, (0, 0, 0))
            number_rect = number_surface.get_rect()
            number_rect.centerx = center_x
            number_rect.centery = center_y - 8
            
            # White background for number
            number_bg = number_rect.inflate(4, 2)
            pygame.draw.rect(self.screen, (255, 255, 255), number_bg)
            pygame.draw.rect(self.screen, (0, 0, 0), number_bg, 1)
            self.screen.blit(number_surface, number_rect)
            
            # Draw cell level at bottom with white background for visibility
            level_text = f"L{cell.level}"
            level_surface = self.font_small.render(level_text, True, (0, 0, 0))
            level_rect = level_surface.get_rect()
            level_rect.centerx = center_x
            level_rect.centery = center_y + 8
            
            # White background rectangle for level text
            level_bg = level_rect.inflate(6, 3)
            pygame.draw.rect(self.screen, (255, 255, 255), level_bg)
            pygame.draw.rect(self.screen, (0, 0, 0), level_bg, 1)
            self.screen.blit(level_surface, level_rect)
            
    def render_nanos(self, game_state: GameState, play_rect: pygame.Rect, nano_spritesheet):
        """Render all Nanos that are not inside buildings"""
        for nano in game_state.nanos.values():
            # Only render nanos that are outside buildings
            if not nano.inside_building:  # KEY CHANGE: Don't render nanos inside buildings
                x = play_rect.x + int(nano.x)
                y = play_rect.y + int(nano.y)
                
                # Try to use the sprite sheet
                if nano_spritesheet:
                    try:
                        sprite_rect = nano.get_animation_rect()
                        nano_surface = nano_spritesheet.subsurface(sprite_rect)
                        self.screen.blit(nano_surface, (x - 8, y - 8))
                    except Exception as e:
                        # Fallback to colored letters if sprite fails
                        self.render_nano_fallback(nano, x, y)
                else:
                    # Fallback to colored letters
                    self.render_nano_fallback(nano, x, y)
                    
                # Draw selection indicator
                if nano.selected:
                    pygame.draw.circle(self.screen, self.accent_color, (x, y), 12, 2)
                    
                # Draw health/happiness bars if low
                if nano.health < 50 or nano.happy < 50:
                    bar_y = y - 20
                    if nano.health < 50:
                        self.draw_progress_bar(x - 8, bar_y, 16, 3, nano.health, 100, self.error_color)
                        bar_y -= 5
                    if nano.happy < 50:
                        self.draw_progress_bar(x - 8, bar_y, 16, 3, nano.happy, 100, self.warning_color)
                    
    def render_nano_fallback(self, nano: Nano, x: int, y: int):
        """Render nano as colored letter fallback"""
        colors = ['red', 'blue', 'green', 'yellow', 'magenta', 'cyan', 'white', 'orange', 'purple', 'pink']
        color_name = colors[nano.id % len(colors)]
        color_map = {
            'red': (255, 0, 0), 'blue': (0, 0, 255), 'green': (0, 255, 0),
            'yellow': (255, 255, 0), 'magenta': (255, 0, 255), 'cyan': (0, 255, 255),
            'white': (255, 255, 255), 'orange': (255, 165, 0), 'purple': (128, 0, 128),
            'pink': (255, 192, 203)
        }
        color = color_map.get(color_name, (255, 255, 255))
        self.draw_text("i", self.font_medium, color, x - 4, y - 8)

    def render_debris(self, debris_objects: List[Dict], game):
        """Render debris from dead nanos"""
        play_rect = getattr(self, 'current_play_rect', None)
        if not play_rect:
            # Fallback calculation if play_rect not set yet
            play_rect = pygame.Rect(
                UI_PANEL_WIDTH + 10,
                TIME_BAR_HEIGHT + 10,
                self.screen_width - UI_PANEL_WIDTH - INFO_PANEL_WIDTH - 30,
                self.screen_height - TIME_BAR_HEIGHT - 100
            )
        
        for debris in debris_objects:
            x = play_rect.x + int(debris['x'])
            y = play_rect.y + int(debris['y'])
            
            # Draw debris as small dark red square
            debris_rect = pygame.Rect(x - 4, y - 4, 8, 8)
            pygame.draw.rect(self.screen, debris['color'], debris_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), debris_rect, 1)
            
            # Draw small "X" on debris
            pygame.draw.line(self.screen, (255, 255, 255), 
                           (x - 3, y - 3), (x + 3, y + 3), 1)
            pygame.draw.line(self.screen, (255, 255, 255), 
                           (x - 3, y + 3), (x + 3, y - 3), 1)

    def render_power_effects(self, power_effects: List[Dict], game):
        """Render power effect animations with energy.png sprites"""
        energy_asset = game.assets.get('power.png')  # power.png is our energy sprite
        
        for effect in power_effects:
            x = int(effect['x'])
            y = int(effect['y'])
            
            if energy_asset:
                # Use the actual energy sprite - SCALE IT DOWN TO 1/10 SIZE
                try:
                    # Scale the sprite to 1/10 size
                    original_size = energy_asset.get_size()
                    scale_factor = effect.get('scale', 1.0) * 0.1  # 1/10 size
                    new_size = (max(1, int(original_size[0] * scale_factor)), 
                               max(1, int(original_size[1] * scale_factor)))
                    scaled_sprite = pygame.transform.scale(energy_asset, new_size)
                    
                    # Center the scaled sprite
                    sprite_rect = scaled_sprite.get_rect()
                    sprite_rect.center = (x, y)
                    self.screen.blit(scaled_sprite, sprite_rect)
                        
                except Exception as e:
                    # Fallback to colored circle
                    self.render_power_effect_fallback(effect)
            else:
                # Fallback to colored circle if no sprite
                self.render_power_effect_fallback(effect)
                
    def render_power_effect_fallback(self, effect: Dict):
        """Render power effect as colored circle fallback"""
        x = int(effect['x'])
        y = int(effect['y'])
        scale = effect.get('scale', 1.0)
        radius = max(3, int(8 * scale))
        
        if effect['phase'] == 'hovering':
            color = (255, 255, 100)  # Bright yellow while hovering
        elif effect['phase'] == 'moving':
            color = (100, 255, 255)  # Cyan while moving
        else:
            color = (255, 255, 255)  # White otherwise
            
        pygame.draw.circle(self.screen, color, (x, y), radius)
        pygame.draw.circle(self.screen, (255, 255, 255), (x, y), radius, 2)
                    
    def render_build_preview(self, game, play_rect: pygame.Rect):
        """Render build preview at mouse position"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if play_rect.collidepoint(mouse_x, mouse_y):
            grid_x = (mouse_x - play_rect.x) // GRID_SIZE
            grid_y = (mouse_y - play_rect.y) // GRID_SIZE
            
            x = play_rect.x + grid_x * GRID_SIZE
            y = play_rect.y + grid_y * GRID_SIZE
            preview_rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
            
            # Check if position is valid
            if game.is_valid_build_position(grid_x, grid_y):
                preview_color = (0, 255, 0, 128)  # Green transparent
            else:
                preview_color = (255, 0, 0, 128)  # Red transparent
                
            # Create transparent surface
            preview_surface = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
            preview_surface.fill(preview_color)
            self.screen.blit(preview_surface, (x, y))
            
    def render_left_panel(self, game_state: GameState, game):
        """Render the left control panel"""
        panel_rect = pygame.Rect(0, TIME_BAR_HEIGHT, UI_PANEL_WIDTH, 
                                self.screen_height - TIME_BAR_HEIGHT)
        pygame.draw.rect(self.screen, self.panel_color, panel_rect)
        
        # Title
        self.draw_text("NANOVERSE", self.font_title, self.accent_color, 10, TIME_BAR_HEIGHT + 10)
        self.draw_text("BATTERY", self.font_title, self.accent_color, 10, TIME_BAR_HEIGHT + 35)
        
        # Main buttons with dynamic tooltips
        button_y = TIME_BAR_HEIGHT + 70
        
        # Calculate upgrade costs for tooltip
        work_level = int(game_state.resources.work_power)
        decimal_part = game_state.resources.work_power - work_level
        decimal_steps = int(decimal_part * 10)
        eu_cost = max(1.0, float(work_level))
        credits_cost = (work_level * 100) + 100 + (decimal_steps * 10)
        
        button_info = [
            ("WORK", f"Produce {game_state.resources.work_power:.1f} EU"),
            ("UPGD", f"Cost: {eu_cost:.0f} EU + {credits_cost:.0f} C"),
            ("SELL", f"1 EU = {game_state.resources.sell_rate:.0f} C"),
            ("BUILD", "Build structures"),
            ("HIRE", "Hire workers")
        ]
        
        for i, (button_name, tooltip) in enumerate(button_info):
            button_rect = pygame.Rect(10, button_y + i * 50, 100, 40)
            
            # Simple button drawing
            pygame.draw.rect(self.screen, (100, 100, 100), button_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), button_rect, 2)
            
            # Simple text drawing
            try:
                text_surf = self.font_medium.render(button_name, True, (255, 255, 255))
                text_rect = text_surf.get_rect()
                text_x = button_rect.centerx - text_rect.width // 2
                text_y = button_rect.centery - text_rect.height // 2
                self.screen.blit(text_surf, (text_x, text_y))
            except:
                pass
            
        # Build menu
        if hasattr(game, 'show_build_menu') and game.show_build_menu:
            self.render_build_menu(game_state, game)
            
    def render_build_menu(self, game_state: GameState, game):
        """Render the build menu"""
        menu_x = 120  # Start to the right of main buttons
        menu_y = TIME_BAR_HEIGHT + 70
        categories = ["POWER", "HOME", "BRAIN", "HAPPY", "DEF"]
        
        for i, category in enumerate(categories):
            button_rect = pygame.Rect(menu_x, menu_y + i * 40, 80, 35)
            selected = (hasattr(game, 'build_category') and game.build_category == category)
            
            # Simple button drawing for build menu
            color = (120, 120, 120) if selected else (80, 80, 80)
            pygame.draw.rect(self.screen, color, button_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), button_rect, 2)
            
            # Simple text drawing
            try:
                text_surf = self.font_small.render(category, True, (255, 255, 255))
                text_rect = text_surf.get_rect()
                text_x = button_rect.centerx - text_rect.width // 2
                text_y = button_rect.centery - text_rect.height // 2
                self.screen.blit(text_surf, (text_x, text_y))
            except:
                pass
            
        # Sub-menu
        if hasattr(game, 'build_category') and game.build_category:
            self.render_build_submenu(game_state, game)
            
    def render_build_submenu(self, game_state: GameState, game):
        """Render the build sub-menu"""
        sub_x = 210  # Further to the right
        sub_y = TIME_BAR_HEIGHT + 70
        
        if game.build_category == "POWER":
            # Cell button - show next cell number and cost
            next_cell_number = len(game_state.cells) + 1
            if next_cell_number <= 100:
                cell_text = f"Cell #{next_cell_number}"
                cost_eu, cost_credits = game_state.get_next_cell_cost()
            else:
                cell_text = "Max Cells"
                cost_eu, cost_credits = float('inf'), float('inf')
                
            cell_rect = pygame.Rect(sub_x, sub_y, 100, 30)
            
            # Simple button
            button_color = (100, 100, 100) if next_cell_number <= 100 else (60, 60, 60)
            pygame.draw.rect(self.screen, button_color, cell_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), cell_rect, 2)
            text_surf = self.font_small.render(cell_text, True, (255, 255, 255))
            text_rect = text_surf.get_rect()
            text_x = cell_rect.centerx - text_rect.width // 2
            text_y = cell_rect.centery - text_rect.height // 2
            self.screen.blit(text_surf, (text_x, text_y))
            
            # Show cost below if not at max
            if next_cell_number <= 100:
                cost_text = f"{cost_eu:.0f} EU"
                self.draw_text(cost_text, self.font_small, (200, 200, 200), sub_x, sub_y + 32)
            
            # BIO generator
            bio_rect = pygame.Rect(sub_x, sub_y + 35, 100, 30)
            pygame.draw.rect(self.screen, (100, 100, 100), bio_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), bio_rect, 2)
            bio_surf = self.font_small.render("BIO", True, (255, 255, 255))
            bio_text_rect = bio_surf.get_rect()
            bio_x = bio_rect.centerx - bio_text_rect.width // 2
            bio_y = bio_rect.centery - bio_text_rect.height // 2
            self.screen.blit(bio_surf, (bio_x, bio_y))
            
        elif game.build_category == "HOME":
            tent_rect = pygame.Rect(sub_x, sub_y, 100, 30)
            pygame.draw.rect(self.screen, (100, 100, 100), tent_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), tent_rect, 2)
            tent_surf = self.font_small.render("TENT", True, (255, 255, 255))
            tent_text_rect = tent_surf.get_rect()
            tent_x = tent_rect.centerx - tent_text_rect.width // 2
            tent_y = tent_rect.centery - tent_text_rect.height // 2
            self.screen.blit(tent_surf, (tent_x, tent_y))
            
        elif game.build_category == "BRAIN":
            study_rect = pygame.Rect(sub_x, sub_y, 100, 30)
            pygame.draw.rect(self.screen, (100, 100, 100), study_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), study_rect, 2)
            study_surf = self.font_small.render("STUDY", True, (255, 255, 255))
            study_text_rect = study_surf.get_rect()
            study_x = study_rect.centerx - study_text_rect.width // 2
            study_y = study_rect.centery - study_text_rect.height // 2
            self.screen.blit(study_surf, (study_x, study_y))
            
        elif game.build_category == "HAPPY":
            music_rect = pygame.Rect(sub_x, sub_y, 100, 30)
            pygame.draw.rect(self.screen, (100, 100, 100), music_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), music_rect, 2)
            music_surf = self.font_small.render("MUSIC", True, (255, 255, 255))
            music_text_rect = music_surf.get_rect()
            music_x = music_rect.centerx - music_text_rect.width // 2
            music_y = music_rect.centery - music_text_rect.height // 2
            self.screen.blit(music_surf, (music_x, music_y))
            
        elif game.build_category == "DEF":
            camp_rect = pygame.Rect(sub_x, sub_y, 100, 30)
            pygame.draw.rect(self.screen, (100, 100, 100), camp_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), camp_rect, 2)
            camp_surf = self.font_small.render("CAMP", True, (255, 255, 255))
            camp_text_rect = camp_surf.get_rect()
            camp_x = camp_rect.centerx - camp_text_rect.width // 2
            camp_y = camp_rect.centery - camp_text_rect.height // 2
            self.screen.blit(camp_surf, (camp_x, camp_y))
            
    def render_right_panel(self, game_state: GameState, game):
        """Render the right information panel as LCD screen"""
        panel_rect = pygame.Rect(self.screen_width - INFO_PANEL_WIDTH - 10, TIME_BAR_HEIGHT + 10,
                                INFO_PANEL_WIDTH, self.screen_height - TIME_BAR_HEIGHT - 100)
        
        # LCD screen background - black with slight blue tint
        pygame.draw.rect(self.screen, (0, 0, 0), panel_rect)
        pygame.draw.rect(self.screen, (0, 20, 40), panel_rect, 3)  # Dark blue border
        
        # Add inner border for LCD effect
        inner_rect = panel_rect.inflate(-6, -6)
        pygame.draw.rect(self.screen, (0, 10, 20), inner_rect, 1)
        
        # LCD Panel title with neon green
        neon_green = (0, 255, 100)
        neon_cyan = (0, 255, 255)
        neon_yellow = (255, 255, 0)
        neon_orange = (255, 128, 0)
        
        self.draw_text(">>> INFO PANEL <<<", self.font_medium, neon_green, 
                      panel_rect.x + 10, panel_rect.y + 10)
        
        # Show different content based on mode
        if hasattr(game, 'show_hire_menu') and game.show_hire_menu:
            self.render_hire_panel_lcd(game_state, game, panel_rect)
        elif hasattr(game, 'info_panel_building') and game.info_panel_building:
            self.render_building_info_lcd(game.info_panel_building, game_state, panel_rect)
        elif hasattr(game, 'info_panel_nano') and game.info_panel_nano:
            self.render_nano_info_lcd(game.info_panel_nano, panel_rect)
        else:
            self.render_general_info_lcd(game_state, panel_rect)

    def render_building_info_lcd(self, building, game_state: GameState, panel_rect: pygame.Rect):
        """Render building information in LCD style"""
        y_offset = 40
        
        # LCD colors
        neon_cyan = (0, 255, 255)
        neon_green = (0, 255, 100)
        neon_yellow = (255, 255, 0)
        neon_orange = (255, 128, 0)
        neon_pink = (255, 20, 147)
        
        # Building type names
        type_names = {
            BuildingType.BIO: "BIO GENERATOR",
            BuildingType.TENT: "TENT HOME",
            BuildingType.STUDY: "STUDY CENTER",
            BuildingType.MUSIC: "MUSIC HALL",
            BuildingType.CAMP: "TRAINING CAMP"
        }
        
        # Building descriptions
        descriptions = {
            BuildingType.BIO: "Generates 1 EU/hour per worker",
            BuildingType.TENT: "Houses up to 2 nanos",
            BuildingType.STUDY: "Trains worker skills",
            BuildingType.MUSIC: "Increases nano happiness",
            BuildingType.CAMP: "Trains physical attributes"
        }
        
        building_name = type_names.get(building.type, "UNKNOWN BUILDING")
        building_desc = descriptions.get(building.type, "No description")
        
        # Get worker names
        worker_names = []
        for nano_id in building.workers:
            if nano_id in game_state.nanos:
                nano = game_state.nanos[nano_id]
                worker_names.append(nano.name)
        
        info_lines = [
            (f"BUILDING DATA:", neon_green),
            ("", (0, 0, 0)),
            (f"TYPE: {building_name}", neon_cyan),
            (f"ID: #{building.building_id}", neon_yellow),
            (f"LEVEL: {building.level}", neon_yellow),
            (f"POS: ({building.x}, {building.y})", neon_cyan),
            ("", (0, 0, 0)),
            (f"CAPACITY: {len(building.workers)}/{building.capacity}", neon_orange),
            ("", (0, 0, 0)),
            ("FUNCTION:", neon_green),
            (f"{building_desc}", neon_cyan),
            ("", (0, 0, 0)),
        ]
        
        # Add worker list
        if worker_names:
            info_lines.append(("WORKERS:", neon_green))
            for worker_name in worker_names:
                info_lines.append((f"  {worker_name}", neon_cyan))
        else:
            info_lines.append(("NO WORKERS", neon_orange))
        
        # Add production info for BIO buildings
        if building.type == BuildingType.BIO and len(building.workers) > 0:
            info_lines.append(("", (0, 0, 0)))
            info_lines.append(("PRODUCTION:", neon_green))
            for nano_id in building.workers:
                if nano_id in game_state.nanos:
                    nano = game_state.nanos[nano_id]
                    efficiency = nano.skills[SkillType.WORKER] / 10.0
                    production = 1.0 * efficiency
                    info_lines.append((f"  {nano.name}: {production:.1f} EU/hr", neon_cyan))
        
        for i, (line, color) in enumerate(info_lines):
            if line:  # Skip empty lines
                self.draw_text(line, self.font_small, color,
                              panel_rect.x + 10, panel_rect.y + y_offset + i * 15)
            
    def render_hire_panel_lcd(self, game_state: GameState, game, panel_rect: pygame.Rect):
        """Render hiring panel in LCD style"""
        if game_state.hired_nanos and game_state.current_hire_index < len(game_state.hired_nanos):
            nano = game_state.hired_nanos[game_state.current_hire_index]
            y_offset = 40
            
            # LCD colors
            neon_cyan = (0, 255, 255)
            neon_green = (0, 255, 100)
            neon_yellow = (255, 255, 0)
            neon_orange = (255, 128, 0)
            
            # Nano info with neon styling
            info_lines = [
                ("CANDIDATE DATA:", neon_green),
                ("", (0, 0, 0)),
                (f"ID: {nano.name}", neon_cyan),
                (f"LVL: {nano.level}", neon_yellow),
                (f"WORK: {nano.skills[SkillType.WORKER]}", neon_cyan),
                (f"BRAIN: {nano.skills[SkillType.BRAINER]}", neon_cyan),
                (f"FIX: {nano.skills[SkillType.FIXER]}", neon_cyan),
                (f"SPD: {nano.speed}%", neon_yellow),
                (f"WAGE: {nano.wage:.0f} C/hr", neon_orange),
                (f"MOOD: {nano.happy:.0f}%", neon_green),
                (f"HP: {nano.health:.0f}%", neon_green),
                ("", (0, 0, 0)),
                (f"COST: {nano.get_hire_cost():.0f} C", neon_orange)
            ]
            
            for i, (line, color) in enumerate(info_lines):
                if line:  # Skip empty lines
                    self.draw_text(line, self.font_small, color,
                                  panel_rect.x + 10, panel_rect.y + y_offset + i * 15)
                                  
            # ACCEPT button - neon style
            accept_y = panel_rect.y + y_offset + len(info_lines) * 15 + 10
            accept_rect = pygame.Rect(panel_rect.x + 10, accept_y, 100, 35)
            
            can_afford = game_state.resources.credits >= nano.get_hire_cost()
            button_color = neon_green if can_afford else (100, 0, 0)
            
            # LCD-style button
            pygame.draw.rect(self.screen, (0, 0, 0), accept_rect)
            pygame.draw.rect(self.screen, button_color, accept_rect, 2)
            
            accept_text = ">>> HIRE <<<" if can_afford else ">> BROKE <<"
            text_surf = self.font_medium.render(accept_text, True, button_color)
            text_rect = text_surf.get_rect()
            text_x = accept_rect.centerx - text_rect.width // 2
            text_y = accept_rect.centery - text_rect.height // 2
            self.screen.blit(text_surf, (text_x, text_y))
            
            # Navigation buttons - LCD style
            nav_y = accept_y + 45
            
            # Previous button
            prev_rect = pygame.Rect(panel_rect.x + 10, nav_y, 45, 25)
            pygame.draw.rect(self.screen, (0, 0, 0), prev_rect)
            pygame.draw.rect(self.screen, neon_cyan, prev_rect, 1)
            prev_surf = self.font_small.render("< PREV", True, neon_cyan)
            prev_text_rect = prev_surf.get_rect()
            prev_x = prev_rect.centerx - prev_text_rect.width // 2
            prev_y = prev_rect.centery - prev_text_rect.height // 2
            self.screen.blit(prev_surf, (prev_x, prev_y))
            
            # Next button
            next_rect = pygame.Rect(panel_rect.x + 65, nav_y, 45, 25)
            pygame.draw.rect(self.screen, (0, 0, 0), next_rect)
            pygame.draw.rect(self.screen, neon_cyan, next_rect, 1)
            next_surf = self.font_small.render("NEXT >", True, neon_cyan)
            next_text_rect = next_surf.get_rect()
            next_x = next_rect.centerx - next_text_rect.width // 2
            next_y = next_rect.centery - next_text_rect.height // 2
            self.screen.blit(next_surf, (next_x, next_y))
            
    def render_nano_info_lcd(self, nano: Nano, panel_rect: pygame.Rect):
        """Render detailed Nano information in LCD style"""
        y_offset = 40
        
        # LCD colors
        neon_cyan = (0, 255, 255)
        neon_green = (0, 255, 100)
        neon_yellow = (255, 255, 0)
        neon_orange = (255, 128, 0)
        
        # Show current state info
        state_text = nano.state.value.upper()
        if nano.inside_building:
            state_text += " (IN BUILDING)"
        
        info_lines = [
            (f"NANO: {nano.name}", neon_green),
            (f"LVL: {nano.level}", neon_yellow),
            (f"STATE: {state_text}", neon_cyan),
            ("", (0, 0, 0)),
            ("SKILLS:", neon_green),
            (f"  WORK: {nano.skills[SkillType.WORKER]}", neon_cyan),
            (f"  BRAIN: {nano.skills[SkillType.BRAINER]}", neon_cyan),
            (f"  FIX: {nano.skills[SkillType.FIXER]}", neon_cyan),
            ("", (0, 0, 0)),
            (f"SPD: {nano.speed}%", neon_yellow),
            (f"WAGE: {nano.wage:.0f} C/hr", neon_orange),
            (f"BRAIN: {nano.brain:.1f}", neon_cyan),
            (f"FORCE: {nano.force:.1f}", neon_cyan),
            ("", (0, 0, 0)),
            (f"MOOD: {nano.happy:.0f}%", neon_green if nano.happy >= 50 else neon_orange),
            (f"HP: {nano.health:.0f}%", neon_green if nano.health >= 50 else neon_orange),
            (f"MEALS: {nano.meals_today}/3", neon_cyan),
            ("", (0, 0, 0)),
            (f"POS: ({nano.x:.0f}, {nano.y:.0f})", neon_yellow)
        ]
        
        for i, (line, color) in enumerate(info_lines):
            if line:  # Skip empty lines
                self.draw_text(line, self.font_small, color,
                              panel_rect.x + 10, panel_rect.y + y_offset + i * 15)
                              
    def render_general_info_lcd(self, game_state: GameState, panel_rect: pygame.Rect):
        """Render general game information in LCD style"""
        y_offset = 40
        
        # LCD colors
        neon_cyan = (0, 255, 255)
        neon_green = (0, 255, 100)
        neon_yellow = (255, 255, 0)
        neon_orange = (255, 128, 0)
        
        # Count nanos inside vs outside buildings
        nanos_outside = sum(1 for nano in game_state.nanos.values() if not nano.inside_building)
        nanos_inside = len(game_state.nanos) - nanos_outside
        
        info_lines = [
            ("SYSTEM STATUS:", neon_green),
            ("", (0, 0, 0)),
            (f"NANOS: {len(game_state.nanos)}", neon_cyan),
            (f"  OUTSIDE: {nanos_outside}", neon_cyan),
            (f"  INSIDE: {nanos_inside}", neon_cyan),
            (f"BUILDINGS: {len(game_state.buildings)}", neon_cyan),
            (f"CELLS: {len(game_state.cells)}", neon_cyan),
            ("", (0, 0, 0)),
            (f"KNOWLEDGE: {game_state.resources.know:.1f}", neon_yellow),
            (f"MIL-INTEL: {game_state.resources.milint:.1f}", neon_orange),
            ("", (0, 0, 0)),
            ("INSTRUCTIONS:", neon_green),
            ("* L-CLICK: SELECT", neon_cyan),
            ("* R-CLICK: INFO", neon_cyan),
            ("* R-CLICK HUB: +1000 C", neon_yellow),
            ("* BUILD: CONSTRUCT", neon_cyan),
            ("* HIRE: ADD WORKERS", neon_cyan),
        ]
        
        for i, (line, color) in enumerate(info_lines):
            if line:  # Skip empty lines
                self.draw_text(line, self.font_small, color,
                              panel_rect.x + 10, panel_rect.y + y_offset + i * 15)
            
    def render_hire_panel(self, game_state: GameState, game, panel_rect: pygame.Rect):
        """Render the hiring panel"""
        if game_state.hired_nanos and game_state.current_hire_index < len(game_state.hired_nanos):
            nano = game_state.hired_nanos[game_state.current_hire_index]
            y_offset = 40
            
            # Nano info
            info_lines = [
                f"Name: {nano.name}",
                f"Level: {nano.level}",
                f"Worker: {nano.skills[SkillType.WORKER]}",
                f"Brainer: {nano.skills[SkillType.BRAINER]}",
                f"Fixer: {nano.skills[SkillType.FIXER]}",
                f"Speed: {nano.speed}%",
                f"Wage: {nano.wage:.0f} C/hour",
                f"Happy: {nano.happy:.0f}%",
                f"Health: {nano.health:.0f}%",
                "",
                f"Hire Cost: {nano.get_hire_cost():.0f} C"
            ]
            
            for i, line in enumerate(info_lines):
                self.draw_text(line, self.font_small, self.text_color,
                              panel_rect.x + 10, panel_rect.y + y_offset + i * 15)
                              
            # ACCEPT button - make it visible and prominent
            accept_y = panel_rect.y + y_offset + len(info_lines) * 15 + 10
            accept_rect = pygame.Rect(panel_rect.x + 10, accept_y, 100, 35)
            
            can_afford = game_state.resources.credits >= nano.get_hire_cost()
            button_color = (0, 150, 0) if can_afford else (150, 0, 0)
            
            # Draw prominent ACCEPT button
            pygame.draw.rect(self.screen, button_color, accept_rect)
            pygame.draw.rect(self.screen, (255, 255, 255), accept_rect, 2)
            
            accept_text = "ACCEPT" if can_afford else "TOO POOR"
            text_surf = self.font_medium.render(accept_text, True, (255, 255, 255))
            text_rect = text_surf.get_rect()
            text_x = accept_rect.centerx - text_rect.width // 2
            text_y = accept_rect.centery - text_rect.height // 2
            self.screen.blit(text_surf, (text_x, text_y))
            
            # Navigation buttons
            nav_y = accept_y + 45
            
            # Previous button
            prev_rect = pygame.Rect(panel_rect.x + 10, nav_y, 45, 25)
            pygame.draw.rect(self.screen, (100, 100, 100), prev_rect)
            pygame.draw.rect(self.screen, (255, 255, 255), prev_rect, 1)
            prev_surf = self.font_small.render("PREV", True, (255, 255, 255))
            prev_text_rect = prev_surf.get_rect()
            prev_x = prev_rect.centerx - prev_text_rect.width // 2
            prev_y = prev_rect.centery - prev_text_rect.height // 2
            self.screen.blit(prev_surf, (prev_x, prev_y))
            
            # Next button
            next_rect = pygame.Rect(panel_rect.x + 65, nav_y, 45, 25)
            pygame.draw.rect(self.screen, (100, 100, 100), next_rect)
            pygame.draw.rect(self.screen, (255, 255, 255), next_rect, 1)
            next_surf = self.font_small.render("NEXT", True, (255, 255, 255))
            next_text_rect = next_surf.get_rect()
            next_x = next_rect.centerx - next_text_rect.width // 2
            next_y = next_rect.centery - next_text_rect.height // 2
            self.screen.blit(next_surf, (next_x, next_y))
            
    def render_nano_info(self, nano: Nano, panel_rect: pygame.Rect):
        """Render detailed Nano information"""
        y_offset = 40
        
        info_lines = [
            f"Name: {nano.name}",
            f"Level: {nano.level}",
            f"State: {nano.state.value}",
            "",
            "Skills:",
            f"  Worker: {nano.skills[SkillType.WORKER]}",
            f"  Brainer: {nano.skills[SkillType.BRAINER]}",
            f"  Fixer: {nano.skills[SkillType.FIXER]}",
            "",
            f"Speed: {nano.speed}%",
            f"Wage: {nano.wage:.0f} C/hour",
            f"Brain: {nano.brain:.1f}",
            f"Force: {nano.force:.1f}",
            "",
            f"Happy: {nano.happy:.0f}%",
            f"Health: {nano.health:.0f}%",
            f"Meals Today: {nano.meals_today}/3",
            "",
            f"Position: ({nano.x:.0f}, {nano.y:.0f})"
        ]
        
        for i, line in enumerate(info_lines):
            color = self.text_color
            if "Happy:" in line and nano.happy < 50:
                color = self.warning_color
            elif "Health:" in line and nano.health < 50:
                color = self.error_color
                
            self.draw_text(line, self.font_small, color,
                          panel_rect.x + 10, panel_rect.y + y_offset + i * 15)
                          
    def render_general_info(self, game_state: GameState, panel_rect: pygame.Rect):
        """Render general game information"""
        y_offset = 40
        
        info_lines = [
            "Game Statistics:",
            "",
            f"Total Nanos: {len(game_state.nanos)}",
            f"Buildings: {len(game_state.buildings)}",
            f"Power Cells: {len(game_state.cells)}",
            "",
            f"Knowledge: {game_state.resources.know:.1f}",
            f"Military Intel: {game_state.resources.milint:.1f}",
            "",
            "Instructions:",
            "• Left-click to select",
            "• Right-click for info",
            "• Use BUILD menu to construct",
            "• Use HIRE to add workers",
        ]
        
        for i, line in enumerate(info_lines):
            self.draw_text(line, self.font_small, self.text_color,
                          panel_rect.x + 10, panel_rect.y + y_offset + i * 15)
                          
    def render_bottom_status_lcd(self, game_state: GameState):
        """Render the bottom status bar as LCD panel"""
        # Position directly under play area
        play_area = getattr(self, 'current_play_rect', pygame.Rect(UI_PANEL_WIDTH + 10, TIME_BAR_HEIGHT + 10, 600, 400))
        
        status_rect = pygame.Rect(
            play_area.x, 
            play_area.y + play_area.height + 5,  # 5px gap below play area
            play_area.width, 
            75  # Height for status info
        )
        
        # LCD panel background - dark gray/black
        pygame.draw.rect(self.screen, (20, 20, 20), status_rect)
        pygame.draw.rect(self.screen, (60, 60, 60), status_rect, 2)  # Gray border
        
        # Inner border for LCD effect
        inner_rect = status_rect.inflate(-4, -4)
        pygame.draw.rect(self.screen, (40, 40, 40), inner_rect, 1)
        
        # LCD text colors (not neon - more subdued)
        lcd_white = (220, 220, 220)
        lcd_cyan = (100, 200, 220)
        lcd_yellow = (220, 220, 100)
        lcd_green = (100, 220, 100)
        lcd_red = (220, 100, 100)  # For bleed capacitor warning
        
        # Resource display - top row
        y_top = status_rect.y + 10
        x_start = status_rect.x + 15
        
        # Check if cells exist
        has_cells = len(game_state.cells) > 0
        
        # Credits display
        credits_text = f"Credits: {game_state.resources.credits:.0f}"
        self.draw_text(credits_text, self.font_medium, lcd_yellow, x_start, y_top)
        
        # Work Power display
        work_text = f"Work Power: {game_state.resources.work_power:.1f}"
        self.draw_text(work_text, self.font_medium, lcd_white, x_start + 200, y_top)
        
        # Sell Rate display
        sell_text = f"Sell Rate: {game_state.resources.sell_rate:.0f} C/EU"
        self.draw_text(sell_text, self.font_medium, lcd_white, x_start + 380, y_top)
        
        # Bottom row - only show if cells exist
        y_bottom = status_rect.y + 35
        
        if has_cells:
            # Show cell storage with progress bar
            max_capacity = sum(float(cell.level) for cell in game_state.cells.values())
            current_power = sum(getattr(cell, 'stored_energy', 0.0) for cell in game_state.cells.values())
            
            self.draw_text("Cell Storage:", self.font_medium, lcd_green, x_start, y_bottom)
            
            # Progress bar
            bar_x = x_start + 130
            bar_y = y_bottom + 2
            bar_width = 200
            bar_height = 16
            
            # Progress bar background
            bar_bg = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
            pygame.draw.rect(self.screen, (40, 40, 40), bar_bg)
            pygame.draw.rect(self.screen, (80, 80, 80), bar_bg, 1)
            
            # Progress bar fill
            if max_capacity > 0:
                fill_width = int(bar_width * min(1.0, current_power / max_capacity))
                if fill_width > 0:
                    fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
                    pygame.draw.rect(self.screen, lcd_green, fill_rect)
                    
            # Capacity text
            capacity_text = f"{current_power:.1f} / {max_capacity:.1f}"
            self.draw_text(capacity_text, self.font_small, lcd_white, bar_x + bar_width + 10, y_bottom + 2)
        else:
            # Show bleed capacitor warning
            bleed_text = f"Bleed Cap: {game_state.resources.surge_capacitor:.1f} / 1.5 EU"
            self.draw_text(bleed_text, self.font_medium, lcd_red, x_start, y_bottom)
        
    def render_floating_labels(self, floating_labels: List[Dict]):
        """Render floating text labels"""
        if not floating_labels:
            print("No floating labels to render")
            return
            
        print(f"Rendering {len(floating_labels)} floating labels")
        for i, label in enumerate(floating_labels):
            print(f"Label {i}: '{label['text']}' at ({label['x']}, {label['y']}) timer: {label['timer']}")
            
            # Calculate alpha based on remaining time
            alpha_factor = min(1.0, label['timer'] / 3.0)  # Fade over 3 seconds
            alpha = int(255 * alpha_factor)
            
            if alpha > 0:
                x, y = int(label['x']), int(label['y'])
                
                # Draw black outline for visibility
                outline_color = (0, 0, 0)
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx != 0 or dy != 0:
                            outline_surface = self.font_large.render(label['text'], True, outline_color)
                            self.screen.blit(outline_surface, (x + dx, y + dy))
                
                # Draw main text
                text_surface = self.font_large.render(label['text'], True, label['color'])
                if alpha < 255:
                    text_surface.set_alpha(alpha)
                self.screen.blit(text_surface, (x, y))
                print(f"Rendered label '{label['text']}' at ({x}, {y})")
            
    def draw_button(self, rect: pygame.Rect, text: str, tooltip: str = "", 
                   selected: bool = False, enabled: bool = True):
        """Draw a button with text and optional tooltip"""
        # Button color
        if not enabled:
            color = (60, 60, 60)
            text_color = (120, 120, 120)
        elif selected:
            color = self.button_pressed_color
            text_color = self.accent_color
        else:
            # Check if mouse is over button
            mouse_pos = pygame.mouse.get_pos()
            if rect.collidepoint(mouse_pos):
                color = self.button_hover_color
            else:
                color = self.button_color
            text_color = self.text_color
            
        # Draw button
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)
        
        # Draw text
        text_rect = self.font_medium.get_rect(text)
        text_x = rect.centerx - text_rect.width // 2
        text_y = rect.centery - text_rect.height // 2
        self.draw_text(text, self.font_medium, text_color, text_x, text_y)
        
        # Draw tooltip on hover
        if tooltip and rect.collidepoint(pygame.mouse.get_pos()):
            self.draw_tooltip(tooltip, pygame.mouse.get_pos())
            
    def draw_tooltip(self, text: str, pos: Tuple[int, int]):
        """Draw a tooltip near the mouse position"""
        tooltip_surface = self.font_small.render(text, True, self.text_color, self.panel_color)
        tooltip_rect = tooltip_surface.get_rect()
        
        # Position tooltip
        x, y = pos
        x += 10
        y -= tooltip_rect.height + 10
        
        # Keep tooltip on screen
        if x + tooltip_rect.width > self.screen_width:
            x = self.screen_width - tooltip_rect.width - 5
        if y < 0:
            y = pos[1] + 20
            
        tooltip_rect.topleft = (x, y)
        
        # Draw background
        pygame.draw.rect(self.screen, self.panel_color, tooltip_rect.inflate(4, 4))
        pygame.draw.rect(self.screen, self.text_color, tooltip_rect.inflate(4, 4), 1)
        
        # Draw text
        self.screen.blit(tooltip_surface, tooltip_rect)
        
    def draw_progress_bar(self, x: int, y: int, width: int, height: int, 
                         current: float, maximum: float, color: Tuple[int, int, int]):
        """Draw a progress bar"""
        # Background
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (40, 40, 40), bg_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), bg_rect, 1)
        
        # Progress fill
        if maximum > 0:
            progress = min(1.0, current / maximum)
            fill_width = int(width * progress)
            if fill_width > 0:
                fill_rect = pygame.Rect(x, y, fill_width, height)
                pygame.draw.rect(self.screen, color, fill_rect)
                
    def draw_text(self, text: str, font: pygame.font.Font, color: Tuple[int, int, int], 
                 x: int, y: int, cache: bool = True) -> pygame.Rect:
        """Draw text with optional caching"""
        if cache:
            cache_key = (text, font, color)
            if cache_key not in self.text_cache:
                self.text_cache[cache_key] = font.render(text, True, color)
            text_surface = self.text_cache[cache_key]
        else:
            text_surface = font.render(text, True, color)
            
        text_rect = text_surface.get_rect()
        text_rect.topleft = (x, y)
        self.screen.blit(text_surface, text_rect)
        return text_rect
        
    def clear_text_cache(self):
        """Clear the text rendering cache"""
        self.text_cache.clear()
        
    def draw_line_with_arrow(self, start: Tuple[int, int], end: Tuple[int, int], 
                           color: Tuple[int, int, int], width: int = 2):
        """Draw a line with an arrow at the end"""
        pygame.draw.line(self.screen, color, start, end, width)
        
        # Calculate arrow points
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.sqrt(dx*dx + dy*dy)
        
        if length > 0:
            # Normalize
            dx /= length
            dy /= length
            
            # Arrow points
            arrow_length = 10
            arrow_angle = 0.5  # radians
            
            # Left arrow point
            left_x = end[0] - arrow_length * (dx * math.cos(arrow_angle) - dy * math.sin(arrow_angle))
            left_y = end[1] - arrow_length * (dy * math.cos(arrow_angle) + dx * math.sin(arrow_angle))
            
            # Right arrow point
            right_x = end[0] - arrow_length * (dx * math.cos(-arrow_angle) - dy * math.sin(-arrow_angle))
            right_y = end[1] - arrow_length * (dy * math.cos(-arrow_angle) + dx * math.sin(-arrow_angle))
            
            # Draw arrow
            pygame.draw.line(self.screen, color, end, (int(left_x), int(left_y)), width)
            pygame.draw.line(self.screen, color, end, (int(right_x), int(right_y)), width)
            
    def draw_connection_lines(self, game_state: GameState, play_rect: pygame.Rect):
        """Draw connection lines between buildings and assigned workers"""
        for building in game_state.buildings.values():
            building_x = play_rect.x + building.x * GRID_SIZE + GRID_SIZE // 2
            building_y = play_rect.y + building.y * GRID_SIZE + GRID_SIZE // 2
            
            for nano_id in building.workers:
                if nano_id in game_state.nanos:
                    nano = game_state.nanos[nano_id]
                    if not nano.inside_building:  # Only draw lines to visible nanos
                        nano_x = play_rect.x + int(nano.x)
                        nano_y = play_rect.y + int(nano.y)
                        
                        # Draw dashed line
                        self.draw_dashed_line((nano_x, nano_y), (building_x, building_y), 
                                            self.accent_color, 1, 5)
                    
    def draw_dashed_line(self, start: Tuple[int, int], end: Tuple[int, int], 
                        color: Tuple[int, int, int], width: int = 1, dash_length: int = 5):
        """Draw a dashed line"""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance == 0:
            return
            
        dashes = int(distance / (dash_length * 2))
        if dashes == 0:
            pygame.draw.line(self.screen, color, start, end, width)
            return
            
        dx_step = dx / (dashes * 2)
        dy_step = dy / (dashes * 2)
        
        for i in range(dashes):
            dash_start = (
                int(start[0] + i * 2 * dx_step),
                int(start[1] + i * 2 * dy_step)
            )
            dash_end = (
                int(start[0] + (i * 2 + 1) * dx_step),
                int(start[1] + (i * 2 + 1) * dy_step)
            )
            pygame.draw.line(self.screen, color, dash_start, dash_end, width)
            
    def render_energy_flow_visualization(self, game_state: GameState, play_rect: pygame.Rect):
        """Render energy flow between components (optional visual enhancement)"""
        # Show energy flowing from capacitor to cells
        center_x = play_rect.x + play_rect.width // 2
        center_y = play_rect.y + play_rect.height // 2
        
        for cell in game_state.cells.values():
            if cell.active:
                cell_x = play_rect.x + cell.x * GRID_SIZE + GRID_SIZE // 2
                cell_y = play_rect.y + cell.y * GRID_SIZE + GRID_SIZE // 2
                
                # Animate energy particles
                t = pygame.time.get_ticks() * 0.001  # Time in seconds
                particle_progress = (t % 2.0) / 2.0  # 2-second cycle
                
                particle_x = int(center_x + (cell_x - center_x) * particle_progress)
                particle_y = int(center_y + (cell_y - center_y) * particle_progress)
                
                pygame.draw.circle(self.screen, (255, 255, 0), (particle_x, particle_y), 2)
                
    def render_debug_info(self, game_state: GameState):
        """Render debug information (for development)"""
        debug_lines = [
            f"FPS: {pygame.time.Clock().get_fps():.1f}",
            f"Game Hour: {game_state.game_hour}",
            f"Nanos: {len(game_state.nanos)}",
            f"EU Rate: {game_state.resources.work_power:.2f}/click",
            f"Capacitor: {game_state.resources.surge_capacitor:.2f}",
        ]
        
        for i, line in enumerate(debug_lines):
            self.draw_text(line, self.font_small, (255, 255, 255), 
                          self.screen_width - 150, 50 + i * 15, cache=False)
            
    def render_minimap(self, game_state: GameState):
        """Render a minimap of the play area (optional feature)"""
        minimap_size = 100
        minimap_x = self.screen_width - minimap_size - 20
        minimap_y = TIME_BAR_HEIGHT + 20
        
        minimap_rect = pygame.Rect(minimap_x, minimap_y, minimap_size, minimap_size)
        pygame.draw.rect(self.screen, (0, 50, 0), minimap_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), minimap_rect, 1)
        
        # Scale factors
        scale_x = minimap_size / PLAY_AREA_WIDTH
        scale_y = minimap_size / PLAY_AREA_HEIGHT
        
        # Draw buildings on minimap
        for building in game_state.buildings.values():
            mini_x = minimap_x + int(building.x * GRID_SIZE * scale_x)
            mini_y = minimap_y + int(building.y * GRID_SIZE * scale_y)
            pygame.draw.rect(self.screen, (255, 255, 255), 
                           pygame.Rect(mini_x, mini_y, 2, 2))
            
        # Draw nanos on minimap
        for nano in game_state.nanos.values():
            if not nano.inside_building:  # Only show visible nanos on minimap
                mini_x = minimap_x + int(nano.x * scale_x)
                mini_y = minimap_y + int(nano.y * scale_y)
                pygame.draw.circle(self.screen, (255, 0, 0), (mini_x, mini_y), 1)
            
    def get_ui_element_at_position(self, x: int, y: int) -> Optional[str]:
        """Get the UI element at the given position (for tooltips and interactions)"""
        # Check main buttons
        button_areas = {
            "WORK": pygame.Rect(10, 100, 100, 40),
            "UPGD": pygame.Rect(10, 150, 100, 40),
            "SELL": pygame.Rect(10, 200, 100, 40),
            "BUILD": pygame.Rect(10, 250, 100, 40),
            "HIRE": pygame.Rect(10, 300, 100, 40),
        }
        
        for element, rect in button_areas.items():
            if rect.collidepoint(x, y):
                return element
                
        return None
        
    def format_number(self, number: float, decimals: int = 1) -> str:
        """Format numbers for display (K, M, B suffixes)"""
        if number >= 1_000_000_000:
            return f"{number / 1_000_000_000:.{decimals}f}B"
        elif number >= 1_000_000:
            return f"{number / 1_000_000:.{decimals}f}M"
        elif number >= 1_000:
            return f"{number / 1_000:.{decimals}f}K"
        else:
            return f"{number:.{decimals}f}"
            
    def animate_button_press(self, button_rect: pygame.Rect):
        """Animate button press effect"""
        # This could be called when a button is pressed to show visual feedback
        overlay = pygame.Surface((button_rect.width, button_rect.height))
        overlay.fill((255, 255, 255))
        overlay.set_alpha(100)
        self.screen.blit(overlay, button_rect.topleft)
        
    def render_day_night_overlay(self, game_state: GameState):
        """Render day/night overlay only on non-game areas"""
        hour = game_state.game_hour
        
        # Calculate light level based on time (smoother transitions)
        if 6 <= hour <= 8:  # Dawn (6 AM to 8 AM)
            dawn_progress = (hour - 6) / 2.0  # 0 to 1 over 2 hours
            light_level = 0.3 + (0.7 * dawn_progress)  # From 30% to 100%
        elif 8 < hour < 17:  # Full day (8 AM to 5 PM)
            light_level = 1.0  # Full brightness
        elif 17 <= hour <= 19:  # Dusk (5 PM to 7 PM)
            dusk_progress = (hour - 17) / 2.0  # 0 to 1 over 2 hours
            light_level = 1.0 - (0.7 * dusk_progress)  # From 100% to 30%
        else:  # Night (7 PM to 6 AM)
            light_level = 0.3  # Dark night
            
        if light_level < 1.0:
            darkness = int((1.0 - light_level) * 100)  # Max 100 alpha
            
            # Get protected areas that should remain lit
            play_area = getattr(self, 'current_play_rect', None)
            if not play_area:
                # Fallback calculation if play_rect not set yet
                play_area = pygame.Rect(
                    UI_PANEL_WIDTH + 10,
                    TIME_BAR_HEIGHT + 10,
                    self.screen_width - UI_PANEL_WIDTH - INFO_PANEL_WIDTH - 30,
                    self.screen_height - TIME_BAR_HEIGHT - 100
                )
            
            # Bottom status panel area (directly under play area)
            status_panel = pygame.Rect(
                play_area.x, 
                play_area.y + play_area.height,
                play_area.width, 
                80  # Status panel height
            ) if play_area.width > 0 else pygame.Rect(0, 0, 0, 0)
            
            # Define areas to darken (everything except protected areas)
            darken_areas = []
            
            # Left margin (before button panel)
            if UI_PANEL_WIDTH > 0:
                darken_areas.append(pygame.Rect(0, TIME_BAR_HEIGHT, UI_PANEL_WIDTH, self.screen_height - TIME_BAR_HEIGHT))
            
            # Right margin (after info panel) 
            info_panel_start = self.screen_width - INFO_PANEL_WIDTH
            if info_panel_start < self.screen_width:
                darken_areas.append(pygame.Rect(info_panel_start, TIME_BAR_HEIGHT, INFO_PANEL_WIDTH, self.screen_height - TIME_BAR_HEIGHT))
            
            # Bottom area (below status panel)
            if status_panel.height > 0:
                bottom_y = status_panel.y + status_panel.height
                if bottom_y < self.screen_height:
                    darken_areas.append(pygame.Rect(0, bottom_y, self.screen_width, self.screen_height - bottom_y))
            
            # Areas between panels and play area
            if play_area.width > 0:
                # Left gap
                left_gap = pygame.Rect(UI_PANEL_WIDTH, TIME_BAR_HEIGHT, 
                                      play_area.x - UI_PANEL_WIDTH, 
                                      play_area.height)
                if left_gap.width > 0:
                    darken_areas.append(left_gap)
                    
                # Right gap  
                right_gap_x = play_area.x + play_area.width
                right_gap = pygame.Rect(right_gap_x, TIME_BAR_HEIGHT,
                                       info_panel_start - right_gap_x,
                                       play_area.height)
                if right_gap.width > 0:
                    darken_areas.append(right_gap)
            
            # Apply darkness to specified areas only
            overlay_color = (0, 0, 30, darkness)
            for area in darken_areas:
                if area.width > 0 and area.height > 0:
                    overlay = pygame.Surface((area.width, area.height), pygame.SRCALPHA)
                    overlay.fill(overlay_color)
                    self.screen.blit(overlay, area.topleft)
            
    def render_particle_effects(self, effects: List[Dict]):
        """Render particle effects for visual enhancement"""
        for effect in effects:
            if effect['type'] == 'spark':
                pygame.draw.circle(self.screen, effect['color'], 
                                 (int(effect['x']), int(effect['y'])), 
                                 max(1, int(effect['size'])))
            elif effect['type'] == 'line':
                pygame.draw.line(self.screen, effect['color'],
                               effect['start'], effect['end'], 
                               max(1, int(effect['width'])))

#EOF ui.py # 1193 lines