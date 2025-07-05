"""
config.py - Game Configuration and Constants for Nanoverse Battery

This module contains all game configuration settings, constants, and tunable parameters.
All other modules import their configuration values from here.
"""

import os
from typing import Tuple, Dict, Any

# ============================================================================
# GAME METADATA
# ============================================================================

GAME_TITLE = "Nanoverse Battery"
GAME_VERSION = "1.0.0"
GAME_AUTHOR = "Nanoverse Studios"
GAME_DESCRIPTION = "Develop a universe in a box to power a console"

# ============================================================================
# DISPLAY SETTINGS
# ============================================================================

# Window dimensions
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600
MAX_WINDOW_WIDTH = 1920
MAX_WINDOW_HEIGHT = 1080

# Display options
DEFAULT_FULLSCREEN = False
DEFAULT_VSYNC = True
TARGET_FPS = 60
ALLOW_RESIZE = True

# UI Layout dimensions
UI_PANEL_WIDTH = 300      # Left control panel width
INFO_PANEL_WIDTH = 250    # Right info panel width
TIME_BAR_HEIGHT = 50      # Top time bar height
STATUS_BAR_HEIGHT = 80    # Bottom status bar height

# Play area calculations (dynamic based on window size)
PLAY_AREA_WIDTH = WINDOW_WIDTH - UI_PANEL_WIDTH - INFO_PANEL_WIDTH - 30
PLAY_AREA_HEIGHT = WINDOW_HEIGHT - TIME_BAR_HEIGHT - STATUS_BAR_HEIGHT - 20
PLAY_AREA_CENTER_X = PLAY_AREA_WIDTH // 2
PLAY_AREA_CENTER_Y = PLAY_AREA_HEIGHT // 2

# Grid system
GRID_SIZE = 32            # Size of each grid cell in pixels
GRID_ALPHA = 100          # Transparency of grid lines (0-255)

# ============================================================================
# GAME MECHANICS
# ============================================================================

# Starting resources
STARTING_CREDITS = 1000.0
STARTING_EU = 0.0
STARTING_WORK_POWER = 0.1

# Energy system
EU_TO_CREDITS_RATE = 1000.0     # Initial conversion rate
SELL_RATE_DECAY = 0.9           # Rate reduction per sale (90%)
MIN_SELL_RATE = 10.0            # Minimum credits per EU
ENERGY_DISSIPATION_RATE = 0.01  # 1% per game hour when no cells
SURGE_CAPACITOR_MAX = 1000.0    # Maximum energy storage

# Work and upgrades
WORK_BUTTON_EU = 0.1            # EU produced per work button press
UPGRADE_COST = 1.0              # Credits to upgrade work power
UPGRADE_AMOUNT = 0.1            # EU increase per upgrade

# Building costs (EU, Credits)
BUILDING_COSTS = {
    "CELL": (1.0, 100.0),
    "BIO": (10.0, 1000.0),
    "TENT": (10.0, 100.0),
    "STUDY": (10.0, 100.0),
    "MUSIC": (10.0, 500.0),
    "CAMP": (10.0, 250.0)
}

# Building capacities (max workers)
BUILDING_CAPACITIES = {
    "BIO": 1,
    "TENT": 2,
    "STUDY": 3,
    "MUSIC": 5,
    "CAMP": 4
}

# Cell system
MAX_CELLS = 100
CELL_UPGRADE_MULTIPLIER = 1.0   # Level * this = EU cost to upgrade
CELL_POWER_CONSUMPTION = 0.1    # EU per hour per cell

# ============================================================================
# NANO CHARACTERS
# ============================================================================

# Nano attributes
NANO_BASE_SPEED = 50.0          # Base movement speed (pixels per second)
NANO_SPEED_VARIANCE = 0.4       # ±40% speed variation
NANO_BASE_WAGE = 10.0           # Base wage in credits per hour
NANO_HIRE_MULTIPLIER = 10       # Hire cost = wage * this
NANO_MAX_SKILLS = 10            # Maximum skill level
NANO_SKILL_GAIN_RATE = 0.1      # Skill points per hour of training

# Nano needs
NANO_MEALS_PER_DAY = 3          # Required meals
NANO_MEAL_COST = 0.3            # EU per meal
NANO_WORK_HOURS = 8             # Hours worked per day
NANO_SLEEP_HOURS = 8            # Hours slept per day
NANO_FREE_HOURS = 8             # Hours for other activities

# Nano stats
NANO_MAX_HEALTH = 100.0
NANO_MAX_HAPPINESS = 100.0
NANO_MAX_BRAIN = 100.0
NANO_MAX_FORCE = 100.0
NANO_HOMELESS_HAPPINESS_LOSS = 10.0  # Daily happiness loss without home
NANO_STARVE_HEALTH_LOSS = 5.0        # Health loss per missed meal

# Nano movement
NANO_MOVE_SPEED = 100.0         # Pixels per second when moving
NANO_WANDER_CHANCE = 0.01       # Chance per frame to start wandering
NANO_WANDER_DISTANCE = 100.0    # Maximum wander distance

# ============================================================================
# TIME AND ENVIRONMENT
# ============================================================================

# Time system
SECONDS_PER_GAME_HOUR = 60.0    # Real seconds per game hour (60 seconds = 1 hour, so 1 second = 1 minute)
HOURS_PER_GAME_DAY = 24
DAYS_PER_GAME_MONTH = 30
MONTHS_PER_GAME_YEAR = 12

# Day/night cycle
SUNRISE_HOUR = 6
SUNSET_HOUR = 18
DAWN_DURATION = 1               # Hours for sunrise transition
DUSK_DURATION = 1               # Hours for sunset transition

# Weather system
WEATHER_CHANGE_INTERVAL = 600.0 # Seconds between weather changes
WEATHER_TRANSITION_TIME = 30.0  # Seconds for weather transitions
WEATHER_INTENSITY_MIN = 0.3     # Minimum weather intensity
WEATHER_INTENSITY_MAX = 1.0     # Maximum weather intensity

# Weather effects
SOLAR_BOOST_MULTIPLIER = 1.5    # Clear weather solar bonus
SOLAR_REDUCTION_MAX = 0.8       # Maximum solar reduction in bad weather
PRODUCTIVITY_BOOST = 1.2        # Good weather productivity bonus
PRODUCTIVITY_REDUCTION_MAX = 0.4 # Maximum productivity reduction
HAPPINESS_WEATHER_RATE = 1.0    # Happiness change per hour from weather
ENERGY_DRAIN_RATE = 0.1         # EU per hour drain in storms

# Particle effects
RAIN_PARTICLES_PER_SECOND = 50
SNOW_PARTICLES_PER_SECOND = 20
FOG_PARTICLES_PER_SECOND = 5
STORM_PARTICLES_PER_SECOND = 100
PARTICLE_LIFETIME_MIN = 3.0     # Minimum particle life in seconds
PARTICLE_LIFETIME_MAX = 15.0    # Maximum particle life in seconds

# ============================================================================
# AUDIO SETTINGS
# ============================================================================

# Audio system
AUDIO_ENABLED = True
MASTER_VOLUME = 0.7             # 0.0 to 1.0
MUSIC_VOLUME = 0.5              # Background music volume
SFX_VOLUME = 0.8                # Sound effects volume
UI_VOLUME = 0.6                 # UI sound volume

# Audio file settings
AUDIO_FREQUENCY = 44100
AUDIO_SIZE = -16                # 16-bit
AUDIO_CHANNELS = 2              # Stereo
AUDIO_BUFFER = 512

# ============================================================================
# ANIMATION SETTINGS
# ============================================================================

# Nano animations
NANO_ANIMATION_SPEED = 0.5      # Seconds per animation frame
NANO_SPRITE_SIZE = 16           # Width/height of each sprite
NANO_SPRITES_PER_ROW = 15       # Sprites per row in sheet (240/16)
NANO_SPRITES_PER_COL = 8        # Sprites per column in sheet (128/16)
NANO_ANIMATION_FRAMES = 3       # Frames per animation
NANO_DIRECTIONS = 4             # Number of direction sprites

# UI animations
BUTTON_HOVER_SPEED = 5.0        # Speed of button hover effect
FLOATING_LABEL_SPEED = 30.0     # Pixels per second for floating text
FLOATING_LABEL_LIFETIME = 2.0   # Seconds before floating text disappears
PROGRESS_BAR_SMOOTH_SPEED = 5.0 # Speed of progress bar animations

# ============================================================================
# COLORS (RGB tuples)
# ============================================================================

# UI Colors
COLOR_BACKGROUND = (50, 50, 50)         # Main background
COLOR_PANEL = (70, 70, 70)              # UI panels
COLOR_BUTTON = (100, 100, 100)          # Default buttons
COLOR_BUTTON_HOVER = (120, 120, 120)    # Hovered buttons
COLOR_BUTTON_PRESSED = (80, 80, 80)     # Pressed buttons
COLOR_BUTTON_DISABLED = (60, 60, 60)    # Disabled buttons

# Text colors
COLOR_TEXT_PRIMARY = (255, 255, 255)    # Main text
COLOR_TEXT_SECONDARY = (200, 200, 200)  # Secondary text
COLOR_TEXT_ACCENT = (0, 255, 255)       # Accent text (cyan)
COLOR_TEXT_SUCCESS = (0, 255, 0)        # Success messages
COLOR_TEXT_WARNING = (255, 255, 0)      # Warnings
COLOR_TEXT_ERROR = (255, 0, 0)          # Errors

# Game world colors
COLOR_PLAY_AREA = (0, 100, 0)           # Play area background
COLOR_GRID = (0, 120, 0)                # Grid lines (lighter for future roads)
COLOR_GRID_ROAD = (0, 80, 0)            # Road grid lines (darker when built)
COLOR_FENCE = (139, 69, 19)             # Fence around play area
COLOR_CENTER_HUB = (0, 100, 255)        # Central power hub

# Building colors
COLOR_CELL_ACTIVE = (255, 255, 0)       # Active power cells
COLOR_CELL_INACTIVE = (128, 128, 0)     # Inactive power cells
COLOR_BIO_BUILDING = (0, 255, 0)        # BIO generators
COLOR_TENT_BUILDING = (139, 69, 19)     # Tent homes
COLOR_STUDY_BUILDING = (0, 0, 255)      # Study facilities
COLOR_MUSIC_BUILDING = (255, 20, 147)   # Music/happiness buildings
COLOR_CAMP_BUILDING = (128, 128, 128)   # Training camps

# Weather/environment colors
COLOR_SKY_DAY_CLEAR = (135, 206, 235)   # Clear day sky
COLOR_SKY_DAY_CLOUDY = (100, 150, 200)  # Cloudy day sky
COLOR_SKY_DAY_STORM = (70, 100, 150)    # Stormy day sky
COLOR_SKY_NIGHT_CLEAR = (25, 25, 112)   # Clear night sky
COLOR_SKY_NIGHT_CLOUDY = (15, 15, 60)   # Cloudy night sky

# Particle colors
COLOR_RAIN = (100, 150, 255)            # Rain drops
COLOR_SNOW = (255, 255, 255)            # Snow flakes
COLOR_FOG = (200, 200, 200)             # Fog particles

# ============================================================================
# INPUT SETTINGS
# ============================================================================

# Mouse settings
DOUBLE_CLICK_TIME = 0.3         # Seconds for double-click detection
DRAG_THRESHOLD = 5              # Pixels before drag starts
SCROLL_SENSITIVITY = 1.0        # Mouse wheel sensitivity

# Keyboard settings
KEY_REPEAT_DELAY = 500          # Milliseconds before key repeat
KEY_REPEAT_INTERVAL = 50        # Milliseconds between repeats

# ============================================================================
# PERFORMANCE SETTINGS
# ============================================================================

# Rendering
MAX_PARTICLES = 500             # Maximum particles on screen
LOD_DISTANCE = 200              # Level of detail switching distance
VSYNC_ENABLED = True            # Vertical sync
FRAME_SKIP_THRESHOLD = 5        # Skip frames if behind this many

# Memory management
ASSET_CACHE_SIZE = 100 * 1024 * 1024  # 100MB asset cache
TEXTURE_COMPRESSION = False     # Enable texture compression
GARBAGE_COLLECT_INTERVAL = 60.0 # Seconds between garbage collection

# Threading
USE_BACKGROUND_LOADING = True   # Load assets in background
MAX_WORKER_THREADS = 2          # Maximum background threads

# ============================================================================
# DEBUG SETTINGS
# ============================================================================

# Debug flags
DEBUG_MODE = False              # Enable debug features
DEBUG_SHOW_FPS = True           # Show FPS counter
DEBUG_SHOW_GRID = True          # Show grid coordinates
DEBUG_SHOW_COLLISIONS = False   # Show collision boxes
DEBUG_SHOW_PATHS = False        # Show movement paths
DEBUG_VERBOSE_LOGGING = False   # Extra detailed logging

# Debug colors
COLOR_DEBUG_TEXT = (255, 255, 0)        # Debug text
COLOR_DEBUG_COLLISION = (255, 0, 255)   # Collision boxes
COLOR_DEBUG_PATH = (0, 255, 255)        # Movement paths

# ============================================================================
# FILE PATHS
# ============================================================================

# Directory paths (relative to SRC folder)
ASSETS_DIR = "../assets"  # Assets folder is one level up from SRC
LOGS_DIR = "../logs"
SAVES_DIR = "../saves"
CONFIG_DIR = "../config"
TEMP_DIR = "../temp"

# Specific file paths
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.ini")
ASSET_MANIFEST = os.path.join(ASSETS_DIR, "manifest.json")
DEFAULT_SAVE_FILE = os.path.join(SAVES_DIR, "game.save")
LOG_FILE = os.path.join(LOGS_DIR, "nanoverse.log")

# Asset file names (updated to lowercase)
NANO_SPRITESHEET = "nanos.png"
SUN_TEXTURE = "sun.png"
MOON_TEXTURE = "moon.png"
POWER_ICON = "power.png"
TENT_TEXTURE = "tent.png"
SHACK_TEXTURE = "shack.png"
SMALL_HOME_TEXTURE = "small_home.png"
LARGE_HOME_TEXTURE = "large_home.png"

# ============================================================================
# GAME BALANCE
# ============================================================================

# Progression rates
XP_GAIN_WORK = 1.0              # XP per hour of work
XP_GAIN_STUDY = 2.0             # XP per hour of study
XP_GAIN_TRAIN = 1.5             # XP per hour of training
SKILL_XP_REQUIREMENT = 100.0    # XP needed per skill level

# Economic balance
INFLATION_RATE = 0.01           # Daily price increases
DEFLATION_RATE = 0.005          # Daily price decreases
MARKET_VOLATILITY = 0.1         # Price variation range

# Difficulty scaling
DIFFICULTY_EASY = {
    "starting_credits": 2000.0,
    "work_power_bonus": 0.5,
    "building_cost_reduction": 0.8
}
DIFFICULTY_NORMAL = {
    "starting_credits": 1000.0,
    "work_power_bonus": 0.0,
    "building_cost_reduction": 1.0
}
DIFFICULTY_HARD = {
    "starting_credits": 500.0,
    "work_power_bonus": -0.2,
    "building_cost_reduction": 1.2
}

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_config():
    """Validate configuration values for consistency"""
    errors = []
    
    # Window size validation
    if WINDOW_WIDTH < MIN_WINDOW_WIDTH or WINDOW_WIDTH > MAX_WINDOW_WIDTH:
        errors.append(f"WINDOW_WIDTH {WINDOW_WIDTH} out of range {MIN_WINDOW_WIDTH}-{MAX_WINDOW_WIDTH}")
    
    if WINDOW_HEIGHT < MIN_WINDOW_HEIGHT or WINDOW_HEIGHT > MAX_WINDOW_HEIGHT:
        errors.append(f"WINDOW_HEIGHT {WINDOW_HEIGHT} out of range {MIN_WINDOW_HEIGHT}-{MAX_WINDOW_HEIGHT}")
    
    # Grid size validation
    if GRID_SIZE <= 0 or GRID_SIZE > 100:
        errors.append(f"GRID_SIZE {GRID_SIZE} must be between 1 and 100")
    
    # Time validation
    if SECONDS_PER_GAME_HOUR <= 0:
        errors.append("SECONDS_PER_GAME_HOUR must be positive")
    
    # Economic validation
    if STARTING_CREDITS < 0:
        errors.append("STARTING_CREDITS cannot be negative")
    
    if MIN_SELL_RATE >= EU_TO_CREDITS_RATE:
        errors.append("MIN_SELL_RATE must be less than EU_TO_CREDITS_RATE")
    
    return errors

def get_difficulty_settings(difficulty: str) -> Dict[str, Any]:
    """Get settings for specified difficulty level"""
    difficulties = {
        "easy": DIFFICULTY_EASY,
        "normal": DIFFICULTY_NORMAL,
        "hard": DIFFICULTY_HARD
    }
    return difficulties.get(difficulty.lower(), DIFFICULTY_NORMAL)

def get_color_palette() -> Dict[str, Tuple[int, int, int]]:
    """Get all colors as a dictionary for easy access"""
    return {
        # UI Colors
        'background': COLOR_BACKGROUND,
        'panel': COLOR_PANEL,
        'button': COLOR_BUTTON,
        'button_hover': COLOR_BUTTON_HOVER,
        'button_pressed': COLOR_BUTTON_PRESSED,
        'button_disabled': COLOR_BUTTON_DISABLED,
        
        # Text Colors
        'text_primary': COLOR_TEXT_PRIMARY,
        'text_secondary': COLOR_TEXT_SECONDARY,
        'text_accent': COLOR_TEXT_ACCENT,
        'text_success': COLOR_TEXT_SUCCESS,
        'text_warning': COLOR_TEXT_WARNING,
        'text_error': COLOR_TEXT_ERROR,
        
        # World Colors
        'play_area': COLOR_PLAY_AREA,
        'grid': COLOR_GRID,
        'fence': COLOR_FENCE,
        'center_hub': COLOR_CENTER_HUB,  # Fixed: was COLOR_CENTER_SQUARE
        
        # Building Colors
        'cell_active': COLOR_CELL_ACTIVE,
        'cell_inactive': COLOR_CELL_INACTIVE,
        'bio_building': COLOR_BIO_BUILDING,
        'tent_building': COLOR_TENT_BUILDING,
        'study_building': COLOR_STUDY_BUILDING,
        'music_building': COLOR_MUSIC_BUILDING,
        'camp_building': COLOR_CAMP_BUILDING
    }

# ============================================================================
# RUNTIME CONFIG UPDATES
# ============================================================================

def update_display_config(width: int, height: int):
    """Update display-dependent configuration values"""
    global WINDOW_WIDTH, WINDOW_HEIGHT, PLAY_AREA_WIDTH, PLAY_AREA_HEIGHT
    global PLAY_AREA_CENTER_X, PLAY_AREA_CENTER_Y
    
    WINDOW_WIDTH = max(MIN_WINDOW_WIDTH, min(MAX_WINDOW_WIDTH, width))
    WINDOW_HEIGHT = max(MIN_WINDOW_HEIGHT, min(MAX_WINDOW_HEIGHT, height))
    
    PLAY_AREA_WIDTH = WINDOW_WIDTH - UI_PANEL_WIDTH - INFO_PANEL_WIDTH - 30
    PLAY_AREA_HEIGHT = WINDOW_HEIGHT - TIME_BAR_HEIGHT - STATUS_BAR_HEIGHT - 20
    PLAY_AREA_CENTER_X = PLAY_AREA_WIDTH // 2
    PLAY_AREA_CENTER_Y = PLAY_AREA_HEIGHT // 2

def apply_difficulty_settings(difficulty: str):
    """Apply difficulty settings to game configuration"""
    global STARTING_CREDITS, STARTING_WORK_POWER
    
    settings = get_difficulty_settings(difficulty)
    STARTING_CREDITS = settings.get("starting_credits", STARTING_CREDITS)
    
    # Apply work power bonus
    work_bonus = settings.get("work_power_bonus", 0.0)
    STARTING_WORK_POWER = max(0.01, STARTING_WORK_POWER + work_bonus)
    
    # Apply building cost modifier
    cost_modifier = settings.get("building_cost_reduction", 1.0)
    for building_type in BUILDING_COSTS:
        eu_cost, credit_cost = BUILDING_COSTS[building_type]
        BUILDING_COSTS[building_type] = (eu_cost * cost_modifier, credit_cost * cost_modifier)

# Run validation on import
_config_errors = validate_config()
if _config_errors:
    print("Configuration validation errors:")
    for error in _config_errors:
        print(f"  - {error}")

#EOF config.py # 495 lines
