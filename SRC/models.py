"""
models.py - Game Objects and Classes for Nanoverse Battery

This module defines all the core game objects including Nanos, Buildings, Resources, and Cells.
"""

import pygame
import random
import math
from enum import Enum
from typing import List, Dict, Optional, Tuple
from config import *

class SkillType(Enum):
    WORKER = "worker"
    BRAINER = "brainer"
    FIXER = "fixer"

class BuildingType(Enum):
    CELL = "cell"
    BIO = "bio"
    TENT = "tent"
    STUDY = "study"
    MUSIC = "music"
    CAMP = "camp"

class NanoState(Enum):
    IDLE = "idle"
    WORKING = "working"
    SLEEPING = "sleeping"
    LEARNING = "learning"
    TRAINING = "training"
    MOVING = "moving"
    HAPPY_TIME = "happy_time"

class Direction(Enum):
    DOWN = 0  # facing
    LEFT = 1
    RIGHT = 2
    UP = 3    # away/behind

class Resource:
    """Manages game resources like EU, Credits, KNOW, MILINT"""
    def __init__(self):
        self.eu = 0.0
        self.credits = 1000.0  # Starting credits
        self.know = 0.0
        self.milint = 0.0
        self.surge_capacitor = 0.0
        self.work_power = 0.1  # Base work power
        self.sell_rate = 1000.0  # EU to Credits conversion rate
        self.sell_floor = 10.0  # Minimum sell rate
        
    def add_eu(self, amount: float):
        """Add EU to surge capacitor"""
        self.surge_capacitor += amount
        
    def drain_eu(self, amount: float) -> bool:
        """Drain EU from surge capacitor, returns True if successful"""
        if self.surge_capacitor >= amount:
            self.surge_capacitor -= amount
            return True
        return False
        
    def sell_eu(self, amount: float) -> bool:
        """Sell EU for credits"""
        if self.surge_capacitor >= amount:
            self.surge_capacitor -= amount
            credits_earned = amount * self.sell_rate
            self.credits += credits_earned
            # Reduce sell rate by 10% but not below floor
            self.sell_rate = max(self.sell_rate * 0.9, self.sell_floor)
            return True
        return False
        
    def spend_credits(self, amount: float) -> bool:
        """Spend credits, returns True if successful"""
        if self.credits >= amount:
            self.credits -= amount
            return True
        return False
        
    def dissipate_energy(self, cells_count: int, dt: float):
        """Energy dissipation - much slower when under 1.5 EU, no bleed when cells exist"""
        if cells_count == 0:
            # No cells - energy bleeds from surge capacitor
            if self.surge_capacitor <= 1.5:
                # Very slow bleed when under 1.5 EU - 0.001 EU per second (0.06 EU per minute)
                dissipation_rate = 0.001 * dt  # Per second, not per game hour
            else:
                # Faster bleed when over 1.5 EU - 0.5% per second
                dissipation_rate = self.surge_capacitor * 0.005 * dt
            
            self.surge_capacitor = max(0, self.surge_capacitor - dissipation_rate)
        else:
            # Cells exist - NO BLEED from surge capacitor
            # All energy stays in surge capacitor until transferred to cells
            pass

class Cell:
    """Represents a power cell in the game"""
    def __init__(self, cell_number: int, x: int, y: int):
        self.cell_number = cell_number  # 1, 2, 3, etc.
        self.x = x
        self.y = y
        self.level = 1
        self.active = True
        self.stored_energy = 0.0  # Current energy stored in this cell
        
    def get_purchase_cost(self) -> Tuple[float, float]:
        """Returns (EU_cost, Credits_cost) for purchasing this cell"""
        eu_cost = float(self.cell_number)  # Cell #1 = 1 EU, Cell #2 = 2 EU, etc.
        credits_cost = 100.0  # Fixed credit cost
        return eu_cost, credits_cost
        
    def get_upgrade_cost(self) -> Tuple[float, float]:
        """Returns (EU_cost, Credits_cost) for upgrading this cell"""
        eu_cost = float(self.cell_number * self.level)  # Cell #1 L1→L2 = 1 EU, Cell #2 L2→L3 = 4 EU
        credits_cost = self.cell_number * self.level * 100.0
        return eu_cost, credits_cost
        
    def upgrade(self) -> bool:
        """Upgrade the cell level"""
        if self.level < 100:
            self.level += 1
            return True
        return False
        
    def consume_power(self, available_power: float) -> float:
        """Consume power and return amount consumed"""
        consumption = 0.1 * self.cell_number  # Higher numbered cells consume more
        if self.active and available_power >= consumption:
            return consumption
        return 0.0

class Building:
    """Base building class"""
    def __init__(self, building_type: BuildingType, x: int, y: int, level: int = 1):
        self.type = building_type
        self.x = x
        self.y = y
        self.level = level
        self.occupied = False
        self.workers = []  # List of Nano IDs working here
        self.capacity = self.get_capacity()
        self.building_id = None  # Will be set when added to game state
        
    def get_capacity(self) -> int:
        """Get worker capacity for this building"""
        capacities = {
            BuildingType.BIO: 1,
            BuildingType.TENT: 2,
            BuildingType.STUDY: 3,
            BuildingType.MUSIC: 5,
            BuildingType.CAMP: 4
        }
        return capacities.get(self.type, 1)
        
    def get_build_cost(self) -> Tuple[float, float]:
        """Returns (EU_cost, Credits_cost) for building"""
        costs = {
            BuildingType.CELL: (1.0, 100.0),
            BuildingType.BIO: (10.0, 1000.0),
            BuildingType.TENT: (10.0, 100.0),
            BuildingType.STUDY: (10.0, 100.0),
            BuildingType.MUSIC: (10.0, 500.0),
            BuildingType.CAMP: (10.0, 250.0)
        }
        return costs.get(self.type, (1.0, 100.0))
        
    def can_accept_worker(self) -> bool:
        """Check if building can accept more workers"""
        return len(self.workers) < self.capacity
        
    def add_worker(self, nano_id: int) -> bool:
        """Add a worker to this building"""
        if self.can_accept_worker() and nano_id not in self.workers:
            self.workers.append(nano_id)
            return True
        return False
        
    def remove_worker(self, nano_id: int) -> bool:
        """Remove a worker from this building"""
        if nano_id in self.workers:
            self.workers.remove(nano_id)
            return True
        return False

class Nano:
    """Represents a Nano worker in the game"""
    def __init__(self, nano_id: int, name: str = None):
        self.id = nano_id
        self.name = name or f"Nano_{nano_id}"
        self.level = 1
        
        # Age system
        self.age = random.randint(18, 40)  # Start between 18-40 years old
        self.max_lifespan = random.randint(60, 90)  # Live 60-90 years
        
        # Skills
        self.skills = {
            SkillType.WORKER: 1,
            SkillType.BRAINER: 1,
            SkillType.FIXER: 1
        }
        
        # Attributes
        self.speed = random.randint(80, 120)  # 80-120% of base speed
        self.wage = 10.0  # Base wage per hour
        self.happy = 100.0  # Happiness level (0-100)
        self.health = 100.0  # Health level (0-100)
        self.brain = 10.0  # Intelligence
        self.force = 10.0  # Combat/Defense skill
        
        # Position and movement
        self.x = float(PLAY_AREA_CENTER_X)
        self.y = float(PLAY_AREA_CENTER_Y)
        self.target_x = self.x
        self.target_y = self.y
        self.moving = False
        self.direction = Direction.DOWN
        
        # State and schedule
        self.state = NanoState.IDLE
        self.assigned_building = None  # Building ID for work
        self.home_building = None     # Building ID for home
        self.current_building = None  # Building ID currently inside
        self.work_hours = 0
        self.sleep_hours = 0
        self.other_hours = 0
        self.last_meal_time = 0
        self.meals_today = 0
        self.inside_building = False  # True when nano is inside a building
        self.on_grid_path = False     # True when moving on grid lines (normal speed)
        self.on_border_path = False   # True when moving on border (2x speed)
        
        # Activity timers
        self.activity_timer = 0.0
        self.activity_duration = 0.0
        
        # Animation
        self.animation_frame = 0
        self.animation_timer = 0
        
        # Selection
        self.selected = False
        
        # Health tracking
        self.hours_without_food = 0
        self.hours_homeless = 0
        
    def get_hire_cost(self) -> float:
        """Get cost to hire this Nano"""
        return self.wage * 10
        
    def age_one_year(self):
        """Age the nano by one year"""
        self.age += 1
        
        # Age affects stats
        if self.age > 50:
            # Older nanos get slower but wiser
            self.speed = max(50, self.speed - 2)  # Lose 2 speed per year after 50
            self.brain = min(20, self.brain + 0.5)  # Gain wisdom
            
        if self.age > 65:
            # Senior nanos lose health
            self.health = max(50, self.health - 3)  # Lose health in old age
            
    def is_dead(self) -> bool:
        """Check if nano has died of old age or poor health"""
        return self.age >= self.max_lifespan or self.health <= 0
        
    def update_position(self, dt: float):
        """Update Nano position based on movement - straight lines only"""
        if self.moving:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            distance = abs(dx) + abs(dy)  # Manhattan distance
            
            if distance < 2.0:  # Close enough
                self.x = self.target_x
                self.y = self.target_y
                self.moving = False
                self.direction = Direction.DOWN
            else:
                # Move in straight lines (no diagonals)
                move_speed = (self.speed / 100.0) * NANO_MOVE_SPEED * dt
                
                # Move horizontally first, then vertically
                if abs(dx) > 1.0:
                    move_x = move_speed if dx > 0 else -move_speed
                    self.x += move_x
                    self.direction = Direction.RIGHT if dx > 0 else Direction.LEFT
                elif abs(dy) > 1.0:
                    move_y = move_speed if dy > 0 else -move_speed
                    self.y += move_y
                    self.direction = Direction.DOWN if dy > 0 else Direction.UP
                    
    def move_to(self, x: float, y: float):
        """Set target position for movement"""
        self.target_x = x
        self.target_y = y
        self.moving = True
        
    def enter_building(self, building_id: int, buildings: Dict):
        """Enter a building"""
        if building_id in buildings:
            building = buildings[building_id]
            if building.add_worker(self.id):
                self.current_building = building_id
                self.inside_building = True
                return True
        return False
        
    def exit_building(self, buildings: Dict):
        """Exit current building"""
        if self.current_building and self.current_building in buildings:
            building = buildings[self.current_building]
            building.remove_worker(self.id)
            self.current_building = None
            self.inside_building = False
            
    def work(self, building: Building) -> float:
        """Work at a building, returns EU produced"""
        if building.type == BuildingType.BIO:
            # BIO generators produce 1 EU per hour per worker
            efficiency = self.skills[SkillType.WORKER] / 10.0  # Skill affects efficiency
            return 1.0 * efficiency
        return 0.0
        
    def study(self) -> float:
        """Study at a STUDY building, returns KNOW produced"""
        if self.state == NanoState.LEARNING:
            # Improve worker skill
            skill_gain = 0.1
            self.skills[SkillType.WORKER] = min(10, self.skills[SkillType.WORKER] + skill_gain)
            self.brain += 0.05
            return 0.1
        return 0.0
        
    def train(self) -> float:
        """Train at a CAMP building, returns MILINT produced"""
        if self.state == NanoState.TRAINING:
            # Improve physical attributes
            self.force += 0.1
            self.health = min(100, self.health + 0.5)
            return 0.1
        return 0.0
        
    def enjoy_music(self):
        """Enjoy music at MUSIC building"""
        if self.state == NanoState.HAPPY_TIME:
            # Gain happiness
            self.happy = min(100, self.happy + 2.0)
        
    def consume_meal(self, resources: Resource) -> bool:
        """Consume a meal, returns True if successful"""
        if resources.drain_eu(0.3):
            self.meals_today += 1
            self.hours_without_food = 0  # Reset hunger timer
            return True
        else:
            # Didn't eat, lose health and track hunger
            self.health -= 5.0
            self.hours_without_food += 1
            return False
            
    def needs_home(self) -> bool:
        """Check if Nano needs a home"""
        return self.home_building is None
        
    def lose_happiness(self, amount: float = 1.0):
        """Lose happiness"""
        self.happy = max(0, self.happy - amount)
        
    def gain_happiness(self, amount: float = 1.0):
        """Gain happiness"""
        self.happy = min(100, self.happy + amount)
        
    def update_daily_needs(self, game_hour: int):
        """Update daily needs based on game hour"""
        # Reset daily counters at midnight
        if game_hour == 0:
            self.meals_today = 0
            self.work_hours = 0
            self.sleep_hours = 0
            self.other_hours = 0
            
            # Lose happiness if no home
            if self.needs_home():
                self.lose_happiness(10.0)
                self.hours_homeless += 24
                # Lose health if homeless for too long
                if self.hours_homeless >= 48:  # 2 days homeless
                    self.health -= 10.0
            else:
                self.hours_homeless = 0
                
        # Hourly health degradation from starvation
        if self.hours_without_food >= 24:  # Haven't eaten in a day
            self.health -= 2.0  # Gradual health loss from starvation
            self.happy -= 5.0   # Unhappy when starving
            
        # Happiness degradation over time if very low health
        if self.health < 20:
            self.happy -= 1.0
            
    def update_yearly_aging(self, game_year: int, last_year: int):
        """Update aging when a year passes"""
        if game_year > last_year:
            years_passed = game_year - last_year
            for _ in range(years_passed):
                self.age_one_year()
                
    def get_animation_rect(self) -> pygame.Rect:
        """Get the sprite rectangle for animation"""
        # Each character is 16x16 pixels
        char_index = self.id % 10  # 10 characters total (5 top, 5 bottom)
        row = char_index // 5  # 0 for top row, 1 for bottom row
        col = char_index % 5   # 0-4 for column
        
        # Animation frame (0-2 for 3 frames)
        anim_frame = self.animation_frame % 3
        
        # Direction determines the row offset
        direction_offset = self.direction.value
        
        x = (col * 3 + anim_frame) * 16  # 3 frames per character
        y = (row * 4 + direction_offset) * 16  # 4 directions per character
        
        return pygame.Rect(x, y, 16, 16)
        
    def update_animation(self, dt: float):
        """Update animation frame"""
        self.animation_timer += dt
        if self.animation_timer >= 0.5:  # Change frame every 0.5 seconds
            self.animation_timer = 0
            if self.moving:
                self.animation_frame = (self.animation_frame + 1) % 3
            else:
                self.animation_frame = 0  # Static frame when not moving

class GameState:
    """Manages the overall game state"""
    def __init__(self):
        self.resources = Resource()
        self.cells = {}  # Dict of cell_number -> Cell
        self.buildings = {}  # Dict of building_id -> Building
        self.nanos = {}  # Dict of nano_id -> Nano
        self.hired_nanos = []  # List of available Nanos for hire
        
        # Game time - now tracks precise time with minutes
        self.game_hour = 0  # 0-23 hours
        self.game_minute = 0  # 0-59 minutes  
        self.game_day = 0
        self.game_month = 0  # 0-11
        self.game_year = 0
        self.time_accumulator = 0.0
        self.last_year = 0  # Track for aging
        
        # Counters
        self.next_building_id = 1
        self.next_nano_id = 1
        
        # UI state
        self.selected_nano = None
        self.build_menu_open = False
        self.hire_menu_open = False
        self.current_hire_index = 0
        
        # Generate initial hire candidates
        self.generate_hire_candidates()
        
    def generate_hire_candidates(self):
        """Generate random Nanos available for hire"""
        self.hired_nanos.clear()
        for _ in range(5):  # Always have 5 candidates
            nano = self.create_random_nano()
            self.hired_nanos.append(nano)
            
    def create_random_nano(self) -> Nano:
        """Create a random Nano for hiring"""
        nano_id = self.next_nano_id
        self.next_nano_id += 1
        
        names = ["Zyx", "Qor", "Vex", "Nix", "Kol", "Jax", "Ryz", "Pyx", "Mox", "Lux"]
        name = random.choice(names) + str(random.randint(100, 999))
        
        nano = Nano(nano_id, name)
        # Randomize some attributes
        nano.speed = random.randint(80, 120)
        nano.wage = random.randint(8, 15)
        nano.happy = random.randint(80, 100)
        nano.health = random.randint(90, 100)
        
        return nano
        
    def hire_nano(self, nano: Nano) -> bool:
        """Hire a Nano if we have enough credits"""
        cost = nano.get_hire_cost()
        if self.resources.spend_credits(cost):
            # Position nano at center hub when hired
            nano.x = float(PLAY_AREA_CENTER_X)
            nano.y = float(PLAY_AREA_CENTER_Y)
            nano.target_x = nano.x
            nano.target_y = nano.y
            
            self.nanos[nano.id] = nano
            # Remove from hire candidates and add new one
            if nano in self.hired_nanos:
                self.hired_nanos.remove(nano)
                self.hired_nanos.append(self.create_random_nano())
                
            # Start nano moving randomly along grid lines
            self.start_nano_grid_movement(nano)
            return True
        return False
        
    def start_nano_grid_movement(self, nano: Nano):
        """Start a nano moving along grid lines"""
        import random
        # Pick a random grid position to move to
        grid_cols = PLAY_AREA_WIDTH // GRID_SIZE
        grid_rows = PLAY_AREA_HEIGHT // GRID_SIZE
        
        target_grid_x = random.randint(1, grid_cols - 2)
        target_grid_y = random.randint(1, grid_rows - 2)
        
        nano.move_to(target_grid_x * GRID_SIZE + GRID_SIZE // 2, 
                    target_grid_y * GRID_SIZE + GRID_SIZE // 2)
        nano.on_grid_path = True  # Mark as moving on grid

    def find_available_building(self, building_type: BuildingType) -> Optional[int]:
        """Find an available building of specified type"""
        for building_id, building in self.buildings.items():
            if building.type == building_type and building.can_accept_worker():
                return building_id
        return None
        
    def assign_nano_home(self, nano: Nano):
        """Assign a home to a nano if available"""
        if nano.home_building is None:
            home_id = self.find_available_building(BuildingType.TENT)
            if home_id:
                nano.home_building = home_id
                
    def build_cell(self, x: int, y: int) -> bool:
        """Build the next sequential cell at position"""
        next_cell_number = len(self.cells) + 1  # Next cell to purchase
        
        if next_cell_number > 100:  # Max 100 cells
            return False
            
        # Create temporary cell to get cost
        temp_cell = Cell(next_cell_number, x, y)
        cost_eu, cost_credits = temp_cell.get_purchase_cost()
        
        # Use cell energy if cells exist, otherwise use surge capacitor
        has_cells = len(self.cells) > 0
        
        can_afford_eu = False
        if has_cells:
            can_afford_eu = self.drain_cell_energy(cost_eu)
        else:
            can_afford_eu = self.resources.drain_eu(cost_eu)
            
        can_afford_credits = self.resources.spend_credits(cost_credits)
        
        if can_afford_eu and can_afford_credits:
            cell = Cell(next_cell_number, x, y)
            self.cells[next_cell_number] = cell  # Use cell_number as key
            return True
        else:
            # Refund if only one succeeded
            if can_afford_credits:
                self.resources.credits += cost_credits
            return False

    def upgrade_cell(self, cell_number: int) -> bool:
        """Upgrade a specific cell"""
        if cell_number not in self.cells:
            return False
            
        cell = self.cells[cell_number]
        if cell.level >= 100:  # Max level
            return False
            
        cost_eu, cost_credits = cell.get_upgrade_cost()
        
        # Use cell energy if cells exist, otherwise use surge capacitor
        has_cells = len(self.cells) > 0
        
        can_afford_eu = False
        if has_cells:
            can_afford_eu = self.drain_cell_energy(cost_eu)
        else:
            can_afford_eu = self.resources.drain_eu(cost_eu)
            
        can_afford_credits = self.resources.spend_credits(cost_credits)
        
        if can_afford_eu and can_afford_credits:
            cell.level += 1
            return True
        else:
            # Refund if only one succeeded
            if can_afford_credits:
                self.resources.credits += cost_credits
            return False

    def get_next_cell_cost(self) -> Tuple[float, float]:
        """Get cost for the next cell to be purchased"""
        next_cell_number = len(self.cells) + 1
        if next_cell_number > 100:
            return float('inf'), float('inf')
        temp_cell = Cell(next_cell_number, 0, 0)
        return temp_cell.get_purchase_cost()
        
    def update_time(self, dt: float):
        """Update game time - 1 real second = 1 game minute"""
        self.time_accumulator += dt
        
        # Fixed: 1 real second = 1 game minute exactly
        while self.time_accumulator >= 1.0:  # Every real second
            self.time_accumulator -= 1.0
            self.advance_minute()
            
    def advance_minute(self):
        """Advance game time by one minute"""
        self.game_minute += 1
        
        if self.game_minute >= 60:
            self.game_minute = 0
            self.game_hour += 1
            
            # Update all Nanos for new hour
            for nano in self.nanos.values():
                nano.update_daily_needs(self.game_hour)
            
            if self.game_hour >= 24:
                self.game_hour = 0
                self.game_day += 1
                
                if self.game_day >= 30:  # 30 days per month
                    self.game_day = 0
                    self.game_month += 1
                    
                    if self.game_month >= 12:  # 12 months per year
                        self.game_month = 0
                        self.game_year += 1
                        
                        # Age all nanos when year changes
                        for nano in self.nanos.values():
                            nano.update_yearly_aging(self.game_year, self.last_year)
                            
                        self.last_year = self.game_year
                        
    def get_precise_time_progress(self) -> float:
        """Get precise time progress including minutes (0.0 to 1.0 within current hour)"""
        return self.game_minute / 60.0
                
    def is_daytime(self) -> bool:
        """Check if it's currently daytime"""
        return 6 <= self.game_hour < 18
        
    def get_sun_moon_position(self) -> float:
        """Get sun/moon position across the sky with smooth minute progression (0.0 to 1.0)"""
        # Include minutes for smooth movement
        precise_hour = self.game_hour + (self.game_minute / 60.0)
        
        if self.is_daytime():
            # Sun moves from 6 AM to 6 PM (12 hour period)
            if precise_hour >= 6.0:
                return (precise_hour - 6.0) / 12.0
            else:
                return 0.0
        else:
            # Moon moves from 6 PM to 6 AM (12 hour period)
            if precise_hour >= 18.0:
                # Evening: 6 PM (18) to midnight (24)
                return (precise_hour - 18.0) / 12.0
            else:
                # Early morning: midnight (0) to 6 AM (6) 
                return (precise_hour + 6.0) / 12.0
    
    def get_total_system_capacity(self) -> float:
        """Get total energy capacity of all cells"""
        return sum(float(cell.level) for cell in self.cells.values())
    
    def get_total_cell_energy(self) -> float:
        """Get total energy stored in all cells"""
        return sum(getattr(cell, 'stored_energy', 0.0) for cell in self.cells.values())
    
    def get_total_system_energy(self) -> float:
        """Get total energy in system (surge capacitor + all cells)"""
        total_energy = self.resources.surge_capacitor
        for cell in self.cells.values():
            total_energy += getattr(cell, 'stored_energy', 0.0)
        return total_energy
    
    def drain_cell_energy(self, amount: float) -> bool:
        """Drain energy from cells - used after cells are purchased"""
        if len(self.cells) == 0:
            return False
            
        total_available = self.get_total_cell_energy()
        if total_available < amount:
            return False
            
        # Drain proportionally from all cells
        remaining_to_drain = amount
        for cell in self.cells.values():
            if remaining_to_drain <= 0:
                break
                
            cell_energy = getattr(cell, 'stored_energy', 0.0)
            if cell_energy > 0:
                drain_from_cell = min(cell_energy, remaining_to_drain)
                cell.stored_energy = cell_energy - drain_from_cell
                remaining_to_drain -= drain_from_cell
                
        return remaining_to_drain <= 0.001  # Allow for small floating point errors
    
    def sell_cell_energy(self, amount: float) -> bool:
        """Sell energy from cells - used after cells are purchased"""
        if self.drain_cell_energy(amount):
            # Store current rate before it changes
            current_rate = self.resources.sell_rate
            credits_earned = amount * current_rate
            self.resources.credits += credits_earned
            # Reduce sell rate by 10% but not below floor
            self.resources.sell_rate = max(self.resources.sell_rate * 0.9, self.resources.sell_floor)
            return True
        return False
            
    def work_button_pressed(self):
        """Handle WORK button press - adds energy to surge capacitor"""
        has_cells = len(self.cells) > 0
        
        if has_cells:
            # With cells: surge capacitor can hold up to total cell capacity
            total_capacity = self.get_total_system_capacity()
            current_surge_energy = self.resources.surge_capacitor
            
            # Only add energy if surge capacitor is under total cell capacity
            if current_surge_energy < total_capacity:
                energy_to_add = min(self.resources.work_power, total_capacity - current_surge_energy)
                if energy_to_add > 0:
                    self.resources.add_eu(energy_to_add)
        else:
            # No cells: limited to 1.5 EU maximum (original behavior)
            if self.resources.surge_capacitor < 1.5:
                energy_to_add = min(self.resources.work_power, 1.5 - self.resources.surge_capacitor)
                if energy_to_add > 0:
                    self.resources.add_eu(energy_to_add)
        
    def upgrade_button_pressed(self):
        """Handle UPGD button press"""
        if self.resources.spend_credits(1.0):
            self.resources.work_power += 0.1
            
    def build_building(self, building_type: BuildingType, x: int, y: int) -> bool:
        """Build a new building at position"""
        building = Building(building_type, x, y)
        cost_eu, cost_credits = building.get_build_cost()
        
        # Use cell energy if cells exist, otherwise use surge capacitor
        has_cells = len(self.cells) > 0
        
        can_afford_eu = False
        if has_cells:
            can_afford_eu = self.drain_cell_energy(cost_eu)
        else:
            can_afford_eu = self.resources.drain_eu(cost_eu)
            
        can_afford_credits = self.resources.spend_credits(cost_credits)
        
        if can_afford_eu and can_afford_credits:
            building.building_id = self.next_building_id
            self.buildings[self.next_building_id] = building
            self.next_building_id += 1
            return True
        else:
            # Refund if only one succeeded
            if can_afford_credits:
                self.resources.credits += cost_credits
            return False
        
    def distribute_energy_to_cells(self, energy_amount: float):
        """Distribute energy from BIO generators - goes to surge capacitor up to capacity"""
        if energy_amount <= 0:
            return
            
        if len(self.cells) == 0:
            # No cells: energy goes to surge capacitor up to 1.5 EU limit
            if self.resources.surge_capacitor < 1.5:
                energy_to_add = min(energy_amount, 1.5 - self.resources.surge_capacitor)
                if energy_to_add > 0:
                    self.resources.add_eu(energy_to_add)
            return
            
        # With cells: energy goes to surge capacitor up to total cell capacity
        total_capacity = self.get_total_system_capacity()
        current_surge_energy = self.resources.surge_capacitor
        
        if current_surge_energy < total_capacity:
            energy_to_add = min(energy_amount, total_capacity - current_surge_energy)
            if energy_to_add > 0:
                self.resources.add_eu(energy_to_add)
        
    def update_energy_system(self, dt: float):
        """Update energy production and consumption"""
        # First, handle energy dissipation (changed to pass dt)
        self.resources.dissipate_energy(len(self.cells), dt)
        
        # Transfer energy from surge capacitor to cells (SLOWER RATE)
        if self.resources.surge_capacitor > 0 and len(self.cells) > 0:
            # Slower transfer rate - 0.5 EU per second instead of 2.0
            transfer_rate = 0.5 * dt  # Transfer 0.5 EU per second
            energy_to_transfer = min(self.resources.surge_capacitor, transfer_rate)
            
            if energy_to_transfer > 0:
                # Find cells that need energy
                cells_needing_energy = []
                for cell in self.cells.values():
                    if cell.active:
                        cell_capacity = float(cell.level)
                        current_storage = getattr(cell, 'stored_energy', 0.0)
                        if current_storage < cell_capacity:
                            cells_needing_energy.append(cell)
                
                if cells_needing_energy:
                    # Distribute energy among cells that need it
                    energy_per_cell = energy_to_transfer / len(cells_needing_energy)
                    total_transferred = 0.0
                    
                    for cell in cells_needing_energy:
                        cell_capacity = float(cell.level)
                        current_storage = getattr(cell, 'stored_energy', 0.0)
                        space_available = cell_capacity - current_storage
                        
                        energy_to_add = min(energy_per_cell, space_available)
                        if energy_to_add > 0:
                            cell.stored_energy = current_storage + energy_to_add
                            total_transferred += energy_to_add
                    
                    # Remove transferred energy from surge capacitor
                    if total_transferred > 0:
                        self.resources.surge_capacitor -= total_transferred
        
        # Fast bleed-off for overcapacity cells (keep this part)
        for cell in self.cells.values():
            if hasattr(cell, 'stored_energy'):
                cell_capacity = float(cell.level)
                if cell.stored_energy > cell_capacity:
                    # Bleed off excess energy FAST - 90% per second when over capacity
                    excess = cell.stored_energy - cell_capacity
                    bleed_rate = excess * 0.9 * dt  # 90% of excess per second
                    cell.stored_energy = max(cell_capacity, cell.stored_energy - bleed_rate)
        
        # Work production from BIO generators (goes directly to cells)
        for building in self.buildings.values():
            if building.type == BuildingType.BIO:
                for nano_id in building.workers:
                    if nano_id in self.nanos:
                        nano = self.nanos[nano_id]
                        if nano.state == NanoState.WORKING and nano.inside_building:
                            eu_produced = nano.work(building) * dt / 3600.0  # Per second
                            # BIO production goes directly to cells
                            if eu_produced > 0:
                                self.distribute_energy_to_cells(eu_produced)

#EOF models.py # 734 lines