"""
game.py - Core Game Logic and State Management for Nanoverse Battery

This module handles the main game loop, state management, input processing,
and coordinates all game systems.
"""

import pygame
import math
import random
import logging
from typing import List, Dict, Optional, Tuple
from models import *
from config import *

class InputHandler:
    """Handles all input processing for the game"""
    def __init__(self):
        self.mouse_pos = (0, 0)
        self.mouse_pressed = False
        self.mouse_released = False
        self.right_mouse_pressed = False
        self.right_mouse_released = False
        self.keys_pressed = set()
        self.keys_released = set()
        
    def update(self, events: List[pygame.event.Event]):
        """Update input state based on events"""
        self.mouse_pressed = False
        self.mouse_released = False
        self.right_mouse_pressed = False
        self.right_mouse_released = False
        self.keys_released.clear()
        
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.mouse_pressed = True
                elif event.button == 3:  # Right click
                    self.right_mouse_pressed = True
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left click
                    self.mouse_released = True
                elif event.button == 3:  # Right click
                    self.right_mouse_released = True
                    
            elif event.type == pygame.KEYDOWN:
                self.keys_pressed.add(event.key)
                
            elif event.type == pygame.KEYUP:
                if event.key in self.keys_pressed:
                    self.keys_pressed.remove(event.key)
                self.keys_released.add(event.key)
                
        self.mouse_pos = pygame.mouse.get_pos()

class GameMode(Enum):
    NORMAL = "normal"
    BUILD_CELL = "build_cell"
    BUILD_BUILDING = "build_building"
    MOVE_NANO = "move_nano"

class Game:
    """Main game class that manages all game systems"""
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock):
        self.screen = screen
        self.clock = clock
        self.running = True
        
        # Game state
        self.state = GameState()
        self.input_handler = InputHandler()
        self.mode = GameMode.NORMAL
        self.selected_building_type = None
        self.dragging_nano = None
        self.floating_labels = []  # List of floating text labels
        self.power_effects = []  # List of power effect animations
        self.debris_objects = []  # List of dead nano debris
        
        # Debug mode for conditional logging
        self.debug_mode = False
        
        # UI state
        self.show_build_menu = False
        self.show_hire_menu = False
        self.build_category = None  # POWER, HOME, BRAIN, HAPPY, DEF
        self.info_panel_nano = None  # Nano being displayed in info panel
        self.info_panel_building = None  # Building being displayed in info panel
        
        # Assets (will be loaded by loading.py)
        self.assets = {}
        
        # Screen dimensions (will be updated on resize)
        self.screen_width = WINDOW_WIDTH
        self.screen_height = WINDOW_HEIGHT
        
        # Play area boundaries (use original rect for click detection)
        self.play_area_rect = pygame.Rect(
            UI_PANEL_WIDTH + 10, 
            TIME_BAR_HEIGHT + 10, 
            self.screen_width - UI_PANEL_WIDTH - INFO_PANEL_WIDTH - 30,
            self.screen_height - TIME_BAR_HEIGHT - 100
        )
        
        # Button areas (updated to match the simple UI positions)
        button_y = TIME_BAR_HEIGHT + 70
        self.button_rects = {
            "WORK": pygame.Rect(10, button_y, 100, 40),
            "UPGD": pygame.Rect(10, button_y + 50, 100, 40),
            "SELL": pygame.Rect(10, button_y + 100, 100, 40),
            "BUILD": pygame.Rect(10, button_y + 150, 100, 40),
            "HIRE": pygame.Rect(10, button_y + 200, 100, 40),
        }
        
        # Build menu buttons (positioned to the right of main buttons)
        menu_x = 120
        menu_y = TIME_BAR_HEIGHT + 70
        self.build_menu_rects = {
            "POWER": pygame.Rect(menu_x, menu_y, 80, 35),
            "HOME": pygame.Rect(menu_x, menu_y + 40, 80, 35),
            "BRAIN": pygame.Rect(menu_x, menu_y + 80, 80, 35),
            "HAPPY": pygame.Rect(menu_x, menu_y + 120, 80, 35),
            "DEF": pygame.Rect(menu_x, menu_y + 160, 80, 35),
        }
        
        # Build sub-menu buttons (further to the right)
        sub_x = 210
        sub_y = TIME_BAR_HEIGHT + 70
        self.build_sub_rects = {
            "CELL": pygame.Rect(sub_x, sub_y, 100, 30),
            "BIO": pygame.Rect(sub_x, sub_y + 70, 100, 30),  # Updated position
            "TENT": pygame.Rect(sub_x, sub_y, 100, 30),
            "STUDY": pygame.Rect(sub_x, sub_y, 100, 30),
            "MUSIC": pygame.Rect(sub_x, sub_y, 100, 30),
            "CAMP": pygame.Rect(sub_x, sub_y, 100, 30),
        }
        
        # Info panel area
        self.info_panel_rect = pygame.Rect(
            self.screen_width - INFO_PANEL_WIDTH - 10,
            TIME_BAR_HEIGHT + 10,
            INFO_PANEL_WIDTH,
            PLAY_AREA_HEIGHT
        )
        
        # Hire panel buttons (positioned in info panel)
        info_panel_x = self.screen_width - INFO_PANEL_WIDTH - 10
        accept_y = TIME_BAR_HEIGHT + 250
        nav_y = accept_y + 45
        
        self.hire_panel_rects = {
            "ACCEPT": pygame.Rect(info_panel_x + 10, accept_y, 100, 35),
            "PREV": pygame.Rect(info_panel_x + 10, nav_y, 45, 25),
            "NEXT": pygame.Rect(info_panel_x + 65, nav_y, 45, 25),
        }
        
    def update(self, dt: float):
        """Update all game systems"""
        # Process input first
        self.handle_input()
        
        # Update game state
        self.state.update_time(dt)
        self.state.update_energy_system(dt)
        
        # Update Nanos and check for deaths
        dead_nanos = []
        for nano in self.state.nanos.values():
            nano.update_position(dt)
            nano.update_animation(dt)
            self.update_nano_ai(nano, dt)
            
            # Check if nano died
            if nano.health <= 0:
                dead_nanos.append(nano)
                
        # Handle nano deaths - convert to debris
        for dead_nano in dead_nanos:
            # Create debris object
            debris = {
                'x': dead_nano.x,
                'y': dead_nano.y,
                'name': dead_nano.name,
                'death_time': 0.0,  # How long they've been dead
                'color': (100, 50, 50)  # Dark red for debris
            }
            self.debris_objects.append(debris)
            
            # Remove from game state
            if dead_nano.id in self.state.nanos:
                del self.state.nanos[dead_nano.id]
                
            # Remove from any buildings
            for building in self.state.buildings.values():
                if dead_nano.id in building.workers:
                    building.workers.remove(dead_nano.id)
                    
            # Show death message
            self.add_floating_label(f"{dead_nano.name} died!", 
                                  self.play_area_rect.x + int(dead_nano.x), 
                                  self.play_area_rect.y + int(dead_nano.y), 
                                  color=(255, 0, 0))
            
        # Update floating labels
        self.update_floating_labels(dt)
        
        # Update debris objects
        self.update_debris(dt)
        
        # Update power effects
        self.update_power_effects(dt)
        
        # Check win/lose conditions
        self.check_game_conditions()
        
    def handle_input(self):
        """Process all input"""
        mouse_x, mouse_y = self.input_handler.mouse_pos
        
        # Handle different game modes
        if self.mode == GameMode.NORMAL:
            self.handle_normal_mode_input(mouse_x, mouse_y)
        elif self.mode == GameMode.BUILD_CELL:
            self.handle_build_cell_input(mouse_x, mouse_y)
        elif self.mode == GameMode.BUILD_BUILDING:
            self.handle_build_building_input(mouse_x, mouse_y)
        elif self.mode == GameMode.MOVE_NANO:
            self.handle_move_nano_input(mouse_x, mouse_y)

    def handle_play_area_click(self, mouse_x: int, mouse_y: int):
        """Handle clicks in the play area"""
        play_x = mouse_x - self.play_area_rect.x
        play_y = mouse_y - self.play_area_rect.y
        
        # Check if clicking on central hub (Easter egg work button)
        play_area_center_x = self.play_area_rect.width // 2
        play_area_center_y = self.play_area_rect.height // 2
        
        # Central hub bounds
        hub_size = GRID_SIZE
        hub_left = play_area_center_x - hub_size // 2
        hub_right = play_area_center_x + hub_size // 2
        hub_top = play_area_center_y - hub_size // 2
        hub_bottom = play_area_center_y + hub_size // 2
        
        if hub_left <= play_x <= hub_right and hub_top <= play_y <= hub_bottom:
            # Easter egg - central hub acts as WORK button
            self.state.work_button_pressed()
            self.add_floating_label(f"+{self.state.resources.work_power:.1f} EU", 
                                  mouse_x, mouse_y)
            
            # Create power effect animation with energy.png
            self.create_power_effect(mouse_x, mouse_y, self.state.resources.work_power)
            return
        
        # Check if clicking on a cell (for upgrades) - hexagonal hit detection
        grid_x = play_x // GRID_SIZE
        grid_y = play_y // GRID_SIZE
        
        # Check if there's a cell at this position with hexagonal hit detection
        for cell in self.state.cells.values():
            if cell.x == grid_x and cell.y == grid_y:
                # Calculate center of the hexagonal cell
                center_x = (cell.x * GRID_SIZE) + GRID_SIZE // 2
                center_y = (cell.y * GRID_SIZE) + GRID_SIZE // 2
                
                # Check if click is within hexagonal cell bounds (approximate with circle)
                cell_radius = GRID_SIZE // 2 - 6
                distance = ((play_x - center_x) ** 2 + (play_y - center_y) ** 2) ** 0.5
                
                if distance <= cell_radius:
                    # Specifically check if clicking on the level button area (moved lower)
                    button_width = 32
                    button_height = 16
                    button_x = center_x - button_width // 2
                    button_y = center_y + cell_radius - button_height - 4  # Updated position
                    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
                    
                    # Convert play coordinates to button check
                    if button_rect.collidepoint(play_x, play_y):
                        # Clicked on level button - try to upgrade
                        if self.state.upgrade_cell(cell.cell_number):
                            self.add_floating_label(f"Cell #{cell.cell_number} → L{cell.level}!", 
                                                  mouse_x, mouse_y)
                        else:
                            cost_eu, cost_credits = cell.get_upgrade_cost()
                            self.add_floating_label(f"Need: {cost_eu:.0f} EU + {cost_credits:.0f} C", 
                                                  mouse_x, mouse_y, color=(255, 0, 0))
                    return
        
        # Check if clicking on a Nano (existing code)
        clicked_nano = None
        for nano in self.state.nanos.values():
            if not nano.inside_building:  # Only select visible nanos
                nano_rect = pygame.Rect(nano.x - 8, nano.y - 8, 16, 16)
                if nano_rect.collidepoint(play_x, play_y):
                    clicked_nano = nano
                    break
                    
        if clicked_nano:
            # Select nano and enter move mode
            self.dragging_nano = clicked_nano
            self.mode = GameMode.MOVE_NANO
            clicked_nano.selected = True
            
            # Deselect other nanos
            for nano in self.state.nanos.values():
                if nano != clicked_nano:
                    nano.selected = False

    def handle_play_area_right_click(self, mouse_x: int, mouse_y: int):
        """Handle right clicks in the play area"""
        play_x = mouse_x - self.play_area_rect.x
        play_y = mouse_y - self.play_area_rect.y
        
        # Get grid coordinates for better detection
        grid_x = play_x // GRID_SIZE
        grid_y = play_y // GRID_SIZE
        grid_cols = self.play_area_rect.width // GRID_SIZE
        grid_rows = self.play_area_rect.height // GRID_SIZE
        center_grid_x = grid_cols // 2
        center_grid_y = grid_rows // 2
        
        # Only log in debug mode for performance
        if self.debug_mode:
            logging.debug(f"Right-click: play({play_x}, {play_y}), grid({grid_x}, {grid_y}), center({center_grid_x}, {center_grid_y})")
        
        # Check if right-clicking on central hub (Easter egg) - use grid coordinates with tolerance
        hub_distance = abs(grid_x - center_grid_x) + abs(grid_y - center_grid_y)
        
        if hub_distance <= 1:  # Allow clicking on center or adjacent cells
            # EASTER EGG: Right-clicking central hub gives 1000 credits
            self.state.resources.credits += 1000
            self.add_floating_label("EASTER EGG! +1000 Credits!", 
                                  mouse_x, mouse_y, color=(255, 215, 0))  # Gold color
            # Only log Easter egg in debug mode
            if self.debug_mode:
                logging.info("🎉 EASTER EGG TRIGGERED! 🎉")
            return
        
        # Check if right-clicking on a building
        grid_x = play_x // GRID_SIZE
        grid_y = play_y // GRID_SIZE
        
        for building in self.state.buildings.values():
            if building.x == grid_x and building.y == grid_y:
                # Select building for info panel
                self.info_panel_building = building
                self.info_panel_nano = None  # Clear nano selection
                self.show_hire_menu = False
                return
        
        # Check if right-clicking on a Nano
        for nano in self.state.nanos.values():
            if not nano.inside_building:  # Only check visible nanos
                nano_rect = pygame.Rect(nano.x - 8, nano.y - 8, 16, 16)
                if nano_rect.collidepoint(play_x, play_y):
                    self.info_panel_nano = nano
                    self.info_panel_building = None  # Clear building selection
                    self.show_hire_menu = False
                    break
                    
    def handle_normal_mode_input(self, mouse_x: int, mouse_y: int):
        """Handle input in normal mode"""
        if self.input_handler.mouse_pressed:
            # Check UI buttons
            if self.button_rects["WORK"].collidepoint(mouse_x, mouse_y):
                self.state.work_button_pressed()
                self.add_floating_label(f"+{self.state.resources.work_power:.1f} EU", 
                                      self.button_rects["WORK"].centerx, 
                                      self.button_rects["WORK"].centery)
                
                # Create power effect animation with energy.png
                self.create_power_effect(self.button_rects["WORK"].centerx,
                                       self.button_rects["WORK"].centery,
                                       self.state.resources.work_power)
                
            elif self.button_rects["UPGD"].collidepoint(mouse_x, mouse_y):
                # Fixed upgrade cost calculation 
                current_power = self.state.resources.work_power
                if self.debug_mode:
                    logging.debug(f"UPGD DEBUG: Current work power: {current_power:.2f}")
                
                # For upgrades: EU cost = 1, Credits cost = 100 (simple flat rate)
                eu_cost = 1.0
                credits_cost = 100.0
                
                # Check if player can afford upgrade - check BOTH surge capacitor AND cells
                surge_eu = self.state.resources.surge_capacitor
                cell_eu = self.state.get_total_cell_energy()
                total_eu = surge_eu + cell_eu
                
                if self.debug_mode:
                    logging.debug(f"UPGD DEBUG: Need {eu_cost} EU + {credits_cost} C, Have {total_eu:.2f} EU + {self.state.resources.credits:.0f} C")
                
                can_afford_eu = total_eu >= eu_cost
                can_afford_credits = self.state.resources.credits >= credits_cost
                
                if can_afford_eu and can_afford_credits:
                    # Deduct EU costs - try surge capacitor first, then cells
                    eu_remaining = eu_cost
                    if surge_eu >= eu_remaining:
                        self.state.resources.surge_capacitor -= eu_remaining
                        eu_remaining = 0
                    else:
                        # Take what we can from surge capacitor
                        self.state.resources.surge_capacitor = 0
                        eu_remaining -= surge_eu
                        # Take the rest from cells
                        if eu_remaining > 0:
                            self.state.drain_cell_energy(eu_remaining)
                    
                    # Deduct credits
                    self.state.resources.credits -= credits_cost
                    
                    # Increase work power
                    old_power = self.state.resources.work_power
                    self.state.resources.work_power += 0.1
                    new_power = self.state.resources.work_power
                    if self.debug_mode:
                        logging.debug(f"UPGD DEBUG: Work power increased from {old_power:.2f} to {new_power:.2f}")
                    
                    self.add_floating_label(f"Work Power: {new_power:.1f}", 
                                          self.button_rects["UPGD"].centerx, 
                                          self.button_rects["UPGD"].centery)
                else:
                    missing = []
                    if not can_afford_eu:
                        missing.append(f"{eu_cost:.0f} EU")
                    if not can_afford_credits:
                        missing.append(f"{credits_cost:.0f} C")
                    
                    self.add_floating_label(f"Need: {', '.join(missing)}", 
                                          self.button_rects["UPGD"].centerx, 
                                          self.button_rects["UPGD"].centery, 
                                          color=(255, 0, 0))
                    
            elif self.button_rects["SELL"].collidepoint(mouse_x, mouse_y):
                # Simplified sell logic - always try cells first, then surge capacitor
                surge_eu = self.state.resources.surge_capacitor
                cell_eu = self.state.get_total_cell_energy()
                total_eu = surge_eu + cell_eu
                
                if total_eu >= 1.0:
                    # Store current sell rate before it changes
                    current_sell_rate = self.state.resources.sell_rate
                    
                    # Try to sell from cells first
                    if cell_eu >= 1.0:
                        if self.state.sell_cell_energy(1.0):
                            self.add_floating_label(f"+{current_sell_rate:.0f} C", 
                                                  self.button_rects["SELL"].centerx, 
                                                  self.button_rects["SELL"].centery)
                        else:
                            self.add_floating_label("Cell sale failed!", 
                                                  self.button_rects["SELL"].centerx, 
                                                  self.button_rects["SELL"].centery, 
                                                  color=(255, 0, 0))
                    # Fall back to surge capacitor
                    elif surge_eu >= 1.0:
                        if self.state.resources.sell_eu(1.0):
                            self.add_floating_label(f"+{current_sell_rate:.0f} C", 
                                                  self.button_rects["SELL"].centerx, 
                                                  self.button_rects["SELL"].centery)
                        else:
                            self.add_floating_label("Surge sale failed!", 
                                                  self.button_rects["SELL"].centerx, 
                                                  self.button_rects["SELL"].centery, 
                                                  color=(255, 0, 0))
                    else:
                        self.add_floating_label("Sell error!", 
                                              self.button_rects["SELL"].centerx, 
                                              self.button_rects["SELL"].centery, 
                                              color=(255, 0, 0))
                else:
                    self.add_floating_label("Not enough EU!", 
                                          self.button_rects["SELL"].centerx, 
                                          self.button_rects["SELL"].centery, 
                                          color=(255, 0, 0))
                    
            elif self.button_rects["BUILD"].collidepoint(mouse_x, mouse_y):
                self.show_build_menu = not self.show_build_menu
                self.show_hire_menu = False
                
            elif self.button_rects["HIRE"].collidepoint(mouse_x, mouse_y):
                self.show_hire_menu = not self.show_hire_menu
                self.show_build_menu = False
                
            # Handle build menu (only if showing)
            elif self.show_build_menu:
                self.handle_build_menu_input(mouse_x, mouse_y)
                
            # Handle hire menu (only if showing) - be very specific
            elif self.show_hire_menu:
                # Only handle hire menu if we're actually in the hire panel area
                if mouse_x > self.screen_width - INFO_PANEL_WIDTH:
                    self.handle_hire_menu_input(mouse_x, mouse_y)
                
            # Handle Nano selection in play area
            elif self.play_area_rect.collidepoint(mouse_x, mouse_y):
                self.handle_play_area_click(mouse_x, mouse_y)
                
        # Handle right clicks
        if self.input_handler.right_mouse_pressed:
            # REMOVED: Debug print statements for performance
            if self.play_area_rect.collidepoint(mouse_x, mouse_y):
                self.handle_play_area_right_click(mouse_x, mouse_y)

    def add_floating_label(self, text: str, x: int, y: int, color: Tuple[int, int, int] = (255, 255, 255)):
        """Add a floating text label"""
        label = {
            'text': text,
            'x': float(x),
            'y': float(y),
            'color': color,
            'timer': 3.0,  # Display for 3 seconds
            'vel_y': -20   # Float upward slower
        }
        self.floating_labels.append(label)
        # REMOVED: Print statements for performance
        return label
        
    def update_floating_labels(self, dt: float):
        """Update floating text labels"""
        # REMOVED: Print statements for performance
        for label in self.floating_labels[:]:
            label['timer'] -= dt
            label['y'] += label['vel_y'] * dt
            label['vel_y'] += 10 * dt  # Reduced gravity for better visibility
            
            if label['timer'] <= 0:
                self.floating_labels.remove(label)
                
    def update_debris(self, dt: float):
        """Update debris objects"""
        for debris in self.debris_objects[:]:
            debris['death_time'] += dt
            
            # Remove debris after 30 seconds
            if debris['death_time'] > 30.0:
                self.debris_objects.remove(debris)
                
    def create_power_effect(self, start_x: int, start_y: int, energy_amount: float):
        """Create a power effect animation with energy.png sprite"""
        # Find a random cell to target
        if len(self.state.cells) == 0:
            return
            
        target_cell = random.choice(list(self.state.cells.values()))
        
        # Calculate target position
        target_x = self.play_area_rect.x + target_cell.x * GRID_SIZE + GRID_SIZE // 2
        target_y = self.play_area_rect.y + target_cell.y * GRID_SIZE + GRID_SIZE // 2
        
        # Create power effect with energy amount
        power_effect = {
            'x': float(start_x),
            'y': float(start_y),
            'target_x': float(target_x),
            'target_y': float(target_y),
            'target_cell': target_cell.cell_number,
            'energy_amount': energy_amount,
            'phase': 'hovering',  # hovering, moving, completed
            'timer': 0.0,
            'hover_duration': 0.5,  # Hover for 0.5 seconds
            'scale': 1.0,  # For pulsing effect
            'completed': False
        }
        
        self.power_effects.append(power_effect)
        
    def update_power_effects(self, dt: float):
        """Update power effect animations"""
        for effect in self.power_effects[:]:
            effect['timer'] += dt
            
            if effect['phase'] == 'hovering':
                # Hover and pulse for 0.5 seconds
                effect['scale'] = 1.0 + 0.3 * math.sin(effect['timer'] * 8)  # Pulsing effect
                
                if effect['timer'] >= effect['hover_duration']:
                    effect['phase'] = 'moving'
                    effect['timer'] = 0.0
                    effect['scale'] = 1.0
                    
            elif effect['phase'] == 'moving':
                # Move towards target cell
                move_speed = 300.0  # pixels per second (faster than nano speed)
                
                dx = effect['target_x'] - effect['x']
                dy = effect['target_y'] - effect['y']
                distance = (dx ** 2 + dy ** 2) ** 0.5
                
                if distance < 5:  # Close enough
                    effect['phase'] = 'completed'
                    
                    # Add energy to the target cell immediately
                    if effect['target_cell'] in self.state.cells:
                        cell = self.state.cells[effect['target_cell']]
                        cell_capacity = float(cell.level)
                        current_storage = getattr(cell, 'stored_energy', 0.0)
                        
                        # Fill the cell with the energy amount
                        energy_to_add = min(effect['energy_amount'], cell_capacity - current_storage)
                        if energy_to_add > 0:
                            cell.stored_energy = current_storage + energy_to_add
                            
                    # Mark for removal
                    effect['completed'] = True
                else:
                    # Move towards target
                    move_x = (dx / distance) * move_speed * dt
                    move_y = (dy / distance) * move_speed * dt
                    effect['x'] += move_x
                    effect['y'] += move_y
                    
            # Remove completed effects
            if effect.get('completed', False):
                self.power_effects.remove(effect)
    
    def handle_build_menu_input(self, mouse_x: int, mouse_y: int):
        """Handle build menu input"""
        if self.build_menu_rects["POWER"].collidepoint(mouse_x, mouse_y):
            self.build_category = "POWER"
            
        elif self.build_menu_rects["HOME"].collidepoint(mouse_x, mouse_y):
            self.build_category = "HOME"
            
        elif self.build_menu_rects["BRAIN"].collidepoint(mouse_x, mouse_y):
            self.build_category = "BRAIN"
            
        elif self.build_menu_rects["HAPPY"].collidepoint(mouse_x, mouse_y):
            self.build_category = "HAPPY"
            
        elif self.build_menu_rects["DEF"].collidepoint(mouse_x, mouse_y):
            self.build_category = "DEF"
            
        # Handle sub-menu clicks
        elif self.build_category == "POWER":
            if self.build_sub_rects["CELL"].collidepoint(mouse_x, mouse_y):
                next_cell_number = len(self.state.cells) + 1
                if next_cell_number <= 100:  # Only allow if not at max
                    self.mode = GameMode.BUILD_CELL
                    self.show_build_menu = False
            elif self.build_sub_rects["BIO"].collidepoint(mouse_x, mouse_y):
                self.mode = GameMode.BUILD_BUILDING
                self.selected_building_type = BuildingType.BIO
                self.show_build_menu = False
                
        elif self.build_category == "HOME":
            if self.build_sub_rects["TENT"].collidepoint(mouse_x, mouse_y):
                self.mode = GameMode.BUILD_BUILDING
                self.selected_building_type = BuildingType.TENT
                self.show_build_menu = False
                
        elif self.build_category == "BRAIN":
            if self.build_sub_rects["STUDY"].collidepoint(mouse_x, mouse_y):
                self.mode = GameMode.BUILD_BUILDING
                self.selected_building_type = BuildingType.STUDY
                self.show_build_menu = False
                
        elif self.build_category == "HAPPY":
            if self.build_sub_rects["MUSIC"].collidepoint(mouse_x, mouse_y):
                self.mode = GameMode.BUILD_BUILDING
                self.selected_building_type = BuildingType.MUSIC
                self.show_build_menu = False
                
        elif self.build_category == "DEF":
            if self.build_sub_rects["CAMP"].collidepoint(mouse_x, mouse_y):
                self.mode = GameMode.BUILD_BUILDING
                self.selected_building_type = BuildingType.CAMP
                self.show_build_menu = False

    def handle_hire_menu_input(self, mouse_x: int, mouse_y: int):
        """Handle hire menu input"""
        if self.hire_panel_rects["ACCEPT"].collidepoint(mouse_x, mouse_y):
            if self.state.current_hire_index < len(self.state.hired_nanos):
                nano = self.state.hired_nanos[self.state.current_hire_index]
                if self.state.hire_nano(nano):
                    self.add_floating_label(f"Hired {nano.name}!", 
                                          self.hire_panel_rects["ACCEPT"].centerx, 
                                          self.hire_panel_rects["ACCEPT"].centery)
                else:
                    self.add_floating_label("Not enough Credits!", 
                                          self.hire_panel_rects["ACCEPT"].centerx, 
                                          self.hire_panel_rects["ACCEPT"].centery, 
                                          color=(255, 0, 0))
                    
        elif self.hire_panel_rects["PREV"].collidepoint(mouse_x, mouse_y):
            if self.state.current_hire_index > 0:
                self.state.current_hire_index -= 1
                
        elif self.hire_panel_rects["NEXT"].collidepoint(mouse_x, mouse_y):
            if self.state.current_hire_index < len(self.state.hired_nanos) - 1:
                self.state.current_hire_index += 1

    def handle_build_cell_input(self, mouse_x: int, mouse_y: int):
        """Handle cell building input"""
        if self.input_handler.mouse_pressed:
            if self.play_area_rect.collidepoint(mouse_x, mouse_y):
                # Convert screen coordinates to grid coordinates
                grid_x = (mouse_x - self.play_area_rect.x) // GRID_SIZE
                grid_y = (mouse_y - self.play_area_rect.y) // GRID_SIZE
                
                if self.state.build_cell(grid_x, grid_y):
                    next_cell_number = len(self.state.cells)  # Just built cell
                    self.add_floating_label(f"Cell #{next_cell_number} Built!", mouse_x, mouse_y)
                else:
                    self.add_floating_label("Cannot Build!", mouse_x, mouse_y, color=(255, 0, 0))
                    
            # Exit build mode
            self.mode = GameMode.NORMAL

    def handle_build_building_input(self, mouse_x: int, mouse_y: int):
        """Handle building construction input"""
        if self.input_handler.mouse_pressed:
            if self.play_area_rect.collidepoint(mouse_x, mouse_y):
                # Convert screen coordinates to grid coordinates
                grid_x = (mouse_x - self.play_area_rect.x) // GRID_SIZE
                grid_y = (mouse_y - self.play_area_rect.y) // GRID_SIZE
                
                if self.state.build_building(self.selected_building_type, grid_x, grid_y):
                    self.add_floating_label(f"{self.selected_building_type.value.upper()} Built!", 
                                          mouse_x, mouse_y)
                else:
                    self.add_floating_label("Cannot Build!", mouse_x, mouse_y, color=(255, 0, 0))
                    
            # Exit build mode
            self.mode = GameMode.NORMAL
            self.selected_building_type = None

    def handle_move_nano_input(self, mouse_x: int, mouse_y: int):
        """Handle Nano movement input"""
        if self.input_handler.mouse_pressed:
            if self.play_area_rect.collidepoint(mouse_x, mouse_y) and self.dragging_nano:
                # Move nano to clicked position
                play_x = mouse_x - self.play_area_rect.x
                play_y = mouse_y - self.play_area_rect.y
                self.dragging_nano.move_to(play_x, play_y)
                
            # Exit move mode
            self.mode = GameMode.NORMAL
            self.dragging_nano = None

    def handle_right_click(self, mouse_x: int, mouse_y: int):
        """Handle right clicks in play area"""
        # This is now handled by handle_play_area_right_click
        pass

    def update_nano_ai(self, nano: Nano, dt: float):
        """Update Nano AI behavior - enhanced for building seeking"""
        current_hour = self.state.game_hour
        
        # Update activity timer
        nano.activity_timer += dt
        
        # Handle building entry/exit based on position
        self.check_nano_building_interaction(nano)
        
        # Determine nano's desired activity based on time and needs
        if 8 <= current_hour < 16:  # Work hours (8 AM to 4 PM)
            self.handle_work_time(nano)
        elif 22 <= current_hour or current_hour < 6:  # Sleep hours (10 PM to 6 AM)
            self.handle_sleep_time(nano)
        else:  # Free time (6 AM to 8 AM, 4 PM to 10 PM)
            self.handle_free_time(nano)
            
        # Handle meal times
        if current_hour in [8, 12, 18] and nano.meals_today < 3:
            nano.consume_meal(self.state.resources)
            
    def handle_work_time(self, nano: Nano):
        """Handle nano behavior during work hours"""
        # Try to assign to work building if not assigned
        if nano.assigned_building is None:
            work_building_id = self.state.find_available_building(BuildingType.BIO)
            if work_building_id:
                nano.assigned_building = work_building_id
                
        # Move to work building
        if nano.assigned_building and not nano.inside_building:
            if nano.assigned_building in self.state.buildings:
                building = self.state.buildings[nano.assigned_building]
                target_x = building.x * GRID_SIZE + GRID_SIZE // 2
                target_y = building.y * GRID_SIZE + GRID_SIZE // 2
                
                if not nano.moving:
                    nano.move_to(target_x, target_y)
                    nano.state = NanoState.WORKING
                    
    def handle_sleep_time(self, nano: Nano):
        """Handle nano behavior during sleep hours"""
        # Assign home if needed
        self.state.assign_nano_home(nano)
        
        # Move to home if has one
        if nano.home_building and not nano.inside_building:
            if nano.home_building in self.state.buildings:
                building = self.state.buildings[nano.home_building]
                target_x = building.x * GRID_SIZE + GRID_SIZE // 2
                target_y = building.y * GRID_SIZE + GRID_SIZE // 2
                
                if not nano.moving:
                    nano.move_to(target_x, target_y)
                    nano.state = NanoState.SLEEPING
        else:
            # No home available, wander around
            nano.state = NanoState.IDLE
            if not nano.moving and random.random() < 0.01:
                self.make_nano_wander(nano)
                
    def handle_free_time(self, nano: Nano):
        """Handle nano behavior during free time"""
        # Exit work building if inside one
        if nano.inside_building and nano.current_building:
            building = self.state.buildings.get(nano.current_building)
            if building and building.type == BuildingType.BIO:
                nano.exit_building(self.state.buildings)
                return
                
        # Choose activity based on needs and availability
        if nano.activity_timer >= nano.activity_duration:
            self.choose_free_time_activity(nano)
            
    def choose_free_time_activity(self, nano: Nano):
        """Choose what nano should do in free time"""
        activities = []
        
        # Add activities based on needs and building availability
        if nano.happy < 80:  # Need happiness
            music_building = self.state.find_available_building(BuildingType.MUSIC)
            if music_building:
                activities.append(('MUSIC', music_building))
                
        if nano.skills[SkillType.WORKER] < 5:  # Need learning
            study_building = self.state.find_available_building(BuildingType.STUDY)
            if study_building:
                activities.append(('STUDY', study_building))
                
        if nano.force < 15:  # Need training
            camp_building = self.state.find_available_building(BuildingType.CAMP)
            if camp_building:
                activities.append(('CAMP', camp_building))
                
        # Choose random activity or wander
        if activities and random.random() < 0.7:  # 70% chance to use building
            activity_type, building_id = random.choice(activities)
            self.send_nano_to_building(nano, building_id, activity_type)
        else:
            # Wander around
            nano.state = NanoState.IDLE
            if not nano.moving:
                self.make_nano_wander(nano)
                
    def send_nano_to_building(self, nano: Nano, building_id: int, activity_type: str):
        """Send nano to a specific building for an activity"""
        if building_id in self.state.buildings:
            building = self.state.buildings[building_id]
            target_x = building.x * GRID_SIZE + GRID_SIZE // 2
            target_y = building.y * GRID_SIZE + GRID_SIZE // 2
            
            if not nano.moving:
                nano.move_to(target_x, target_y)
                
                # Set state based on activity
                if activity_type == 'MUSIC':
                    nano.state = NanoState.HAPPY_TIME
                    nano.activity_duration = random.uniform(30, 120)  # 30 seconds to 2 minutes
                elif activity_type == 'STUDY':
                    nano.state = NanoState.LEARNING
                    nano.activity_duration = random.uniform(60, 180)  # 1 to 3 minutes
                elif activity_type == 'CAMP':
                    nano.state = NanoState.TRAINING
                    nano.activity_duration = random.uniform(45, 150)  # 45 seconds to 2.5 minutes
                    
                nano.activity_timer = 0.0
                
    def make_nano_wander(self, nano: Nano):
        """Make nano wander to a random location"""
        # Pick a random grid position to move to - adjusted for larger grid
        grid_cols = PLAY_AREA_WIDTH // GRID_SIZE
        grid_rows = PLAY_AREA_HEIGHT // GRID_SIZE
        
        target_grid_x = random.randint(1, grid_cols - 2)
        target_grid_y = random.randint(1, grid_rows - 2)
        
        nano.move_to(target_grid_x * GRID_SIZE + GRID_SIZE // 2, 
                    target_grid_y * GRID_SIZE + GRID_SIZE // 2)
                    
    def check_nano_building_interaction(self, nano: Nano):
        """Check if nano should enter or exit buildings"""
        if nano.moving:
            return
            
        # Check all buildings for entry
        for building_id, building in self.state.buildings.items():
            building_center_x = building.x * GRID_SIZE + GRID_SIZE // 2
            building_center_y = building.y * GRID_SIZE + GRID_SIZE // 2
            
            # If nano is close to building center
            distance = abs(nano.x - building_center_x) + abs(nano.y - building_center_y)
            if distance < 20:  # Close enough to enter
                # Check if nano should enter this building
                should_enter = False
                
                if building.type == BuildingType.BIO and nano.state == NanoState.WORKING:
                    should_enter = nano.assigned_building == building_id
                elif building.type == BuildingType.TENT and nano.state == NanoState.SLEEPING:
                    should_enter = nano.home_building == building_id
                elif building.type == BuildingType.MUSIC and nano.state == NanoState.HAPPY_TIME:
                    should_enter = True
                elif building.type == BuildingType.STUDY and nano.state == NanoState.LEARNING:
                    should_enter = True
                elif building.type == BuildingType.CAMP and nano.state == NanoState.TRAINING:
                    should_enter = True
                    
                if should_enter and not nano.inside_building:
                    if nano.enter_building(building_id, self.state.buildings):
                        break
                        
        # Handle activity completion and building exit
        if nano.inside_building and nano.current_building:
            building = self.state.buildings.get(nano.current_building)
            if building:
                should_exit = False
                
                # Check if activity is complete or time to leave
                if building.type == BuildingType.MUSIC and nano.activity_timer >= nano.activity_duration:
                    nano.enjoy_music()  # Gain happiness
                    should_exit = True
                elif building.type == BuildingType.STUDY and nano.activity_timer >= nano.activity_duration:
                    nano.study()  # Gain skills
                    should_exit = True
                elif building.type == BuildingType.CAMP and nano.activity_timer >= nano.activity_duration:
                    nano.train()  # Gain physical attributes
                    should_exit = True
                elif building.type == BuildingType.TENT and 6 <= self.state.game_hour < 22:
                    should_exit = True  # Leave home during day
                elif building.type == BuildingType.BIO and not (8 <= self.state.game_hour < 16):
                    should_exit = True  # Leave work outside work hours
                    
                if should_exit:
                    nano.exit_building(self.state.buildings)
                    nano.state = NanoState.IDLE

    def handle_resize(self, width: int, height: int):
        """Handle window resize"""
        self.screen_width = width
        self.screen_height = height
        
        # Update play area position
        self.play_area_rect = pygame.Rect(
            UI_PANEL_WIDTH + 10, 
            TIME_BAR_HEIGHT + 10, 
            width - UI_PANEL_WIDTH - INFO_PANEL_WIDTH - 30,
            height - TIME_BAR_HEIGHT - 100
        )
        
        # Update info panel position
        self.info_panel_rect = pygame.Rect(
            width - INFO_PANEL_WIDTH - 10,
            TIME_BAR_HEIGHT + 10,
            INFO_PANEL_WIDTH,
            height - TIME_BAR_HEIGHT - 100
        )
        
        # Update hire panel button positions
        self.hire_panel_rects["ACCEPT"].x = self.info_panel_rect.x + 10
        self.hire_panel_rects["PREV"].x = self.info_panel_rect.x + 10
        self.hire_panel_rects["NEXT"].x = self.info_panel_rect.x + 55

    def check_game_conditions(self):
        """Check for win/lose conditions"""
        # Example: Lose if all Nanos die
        if len(self.state.nanos) > 0:
            all_dead = all(nano.health <= 0 for nano in self.state.nanos.values())
            if all_dead:
                # Game over logic here
                pass
                
        # Example: Win condition could be reaching certain power levels
        if self.state.resources.surge_capacitor >= 1000:
            # Victory logic here
            pass

    def get_grid_position(self, x: int, y: int) -> Tuple[int, int]:
        """Convert screen coordinates to grid coordinates"""
        grid_x = (x - self.play_area_rect.x) // GRID_SIZE
        grid_y = (y - self.play_area_rect.y) // GRID_SIZE
        return grid_x, grid_y
        
    def get_screen_position(self, grid_x: int, grid_y: int) -> Tuple[int, int]:
        """Convert grid coordinates to screen coordinates"""
        x = self.play_area_rect.x + grid_x * GRID_SIZE
        y = self.play_area_rect.y + grid_y * GRID_SIZE
        return x, y

    def is_valid_build_position(self, grid_x: int, grid_y: int) -> bool:
        """Check if position is valid for building"""
        # Check bounds
        if grid_x < 0 or grid_y < 0:
            return False
        if grid_x >= PLAY_AREA_WIDTH // GRID_SIZE or grid_y >= PLAY_AREA_HEIGHT // GRID_SIZE:
            return False
            
        # Check if position is occupied
        for building in self.state.buildings.values():
            if building.x == grid_x and building.y == grid_y:
                return False
                
        for cell in self.state.cells.values():
            if cell.x == grid_x and cell.y == grid_y:
                return False
                
        return True

    def quit(self):
        """Clean shutdown of the game"""
        self.running = False

#EOF game.py # 778