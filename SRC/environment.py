"""
environment.py - Game World, Time, and Weather Management for Nanoverse Battery

This module manages the game world environment including time progression,
weather systems, environmental effects, and world simulation.
"""

import pygame
import random
import math
from typing import List, Dict, Optional, Tuple
from enum import Enum
from models import *
from config import *

class WeatherType(Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    STORM = "storm"
    FOG = "fog"
    SNOW = "snow"

class SeasonType(Enum):
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"

class EnvironmentalEffect(Enum):
    SOLAR_BOOST = "solar_boost"
    SOLAR_REDUCTION = "solar_reduction"
    ENERGY_DRAIN = "energy_drain"
    HAPPINESS_BOOST = "happiness_boost"
    HAPPINESS_REDUCTION = "happiness_reduction"
    PRODUCTIVITY_BOOST = "productivity_boost"
    PRODUCTIVITY_REDUCTION = "productivity_reduction"

class WeatherSystem:
    """Manages weather patterns and their effects on the game"""
    
    def __init__(self):
        self.current_weather = WeatherType.CLEAR
        self.weather_intensity = 0.5  # 0.0 to 1.0
        self.weather_duration = 0.0
        self.weather_change_timer = 0.0
        self.weather_change_interval = 600.0  # 10 minutes real time
        
        # Weather transition
        self.transitioning = False
        self.transition_progress = 0.0
        self.next_weather = None
        
        # Weather effects
        self.active_effects = []
        
        # Weather patterns (probability weights)
        self.weather_patterns = {
            WeatherType.CLEAR: 0.4,
            WeatherType.CLOUDY: 0.3,
            WeatherType.RAIN: 0.15,
            WeatherType.STORM: 0.05,
            WeatherType.FOG: 0.08,
            WeatherType.SNOW: 0.02
        }
        
    def update(self, dt: float, game_hour: int, season: SeasonType):
        """Update weather system"""
        self.weather_duration += dt
        self.weather_change_timer += dt
        
        # Handle weather transitions
        if self.transitioning:
            self.transition_progress += dt * 2.0  # 0.5 second transition
            if self.transition_progress >= 1.0:
                self.current_weather = self.next_weather
                self.transitioning = False
                self.transition_progress = 0.0
                self.next_weather = None
                self.weather_duration = 0.0
                
        # Check for weather changes
        elif self.weather_change_timer >= self.weather_change_interval:
            self.change_weather(season)
            self.weather_change_timer = 0.0
            
        # Update weather effects
        self.update_effects(dt, game_hour)
        
    def change_weather(self, season: SeasonType):
        """Change to new weather based on season"""
        # Adjust weather patterns based on season
        seasonal_patterns = self.get_seasonal_patterns(season)
        
        # Don't change to same weather
        available_weather = {w: p for w, p in seasonal_patterns.items() 
                           if w != self.current_weather}
        
        if available_weather:
            total_weight = sum(available_weather.values())
            rand_val = random.random() * total_weight
            
            cumulative = 0.0
            for weather, weight in available_weather.items():
                cumulative += weight
                if rand_val <= cumulative:
                    self.start_transition(weather)
                    break
                    
    def get_seasonal_patterns(self, season: SeasonType) -> Dict[WeatherType, float]:
        """Get weather patterns adjusted for season"""
        patterns = self.weather_patterns.copy()
        
        if season == SeasonType.SPRING:
            patterns[WeatherType.RAIN] *= 1.5
            patterns[WeatherType.CLEAR] *= 1.2
            patterns[WeatherType.SNOW] *= 0.1
            
        elif season == SeasonType.SUMMER:
            patterns[WeatherType.CLEAR] *= 1.8
            patterns[WeatherType.STORM] *= 1.3
            patterns[WeatherType.SNOW] = 0.0
            patterns[WeatherType.FOG] *= 0.5
            
        elif season == SeasonType.AUTUMN:
            patterns[WeatherType.CLOUDY] *= 1.4
            patterns[WeatherType.FOG] *= 1.5
            patterns[WeatherType.RAIN] *= 1.2
            patterns[WeatherType.SNOW] *= 0.3
            
        elif season == SeasonType.WINTER:
            patterns[WeatherType.SNOW] *= 5.0
            patterns[WeatherType.CLOUDY] *= 1.3
            patterns[WeatherType.CLEAR] *= 0.7
            patterns[WeatherType.STORM] *= 0.5
            
        return patterns
        
    def start_transition(self, new_weather: WeatherType):
        """Start transitioning to new weather"""
        self.next_weather = new_weather
        self.transitioning = True
        self.transition_progress = 0.0
        
        # Set random intensity for new weather
        self.weather_intensity = random.uniform(0.3, 1.0)
        
    def update_effects(self, dt: float, game_hour: int):
        """Update active weather effects"""
        self.active_effects.clear()
        
        # Apply weather-specific effects
        if self.current_weather == WeatherType.CLEAR:
            if 6 <= game_hour <= 18:  # Daytime
                self.active_effects.append(EnvironmentalEffect.SOLAR_BOOST)
                self.active_effects.append(EnvironmentalEffect.HAPPINESS_BOOST)
                
        elif self.current_weather == WeatherType.CLOUDY:
            self.active_effects.append(EnvironmentalEffect.SOLAR_REDUCTION)
            
        elif self.current_weather == WeatherType.RAIN:
            self.active_effects.append(EnvironmentalEffect.SOLAR_REDUCTION)
            self.active_effects.append(EnvironmentalEffect.HAPPINESS_REDUCTION)
            if self.weather_intensity > 0.7:
                self.active_effects.append(EnvironmentalEffect.PRODUCTIVITY_REDUCTION)
                
        elif self.current_weather == WeatherType.STORM:
            self.active_effects.append(EnvironmentalEffect.SOLAR_REDUCTION)
            self.active_effects.append(EnvironmentalEffect.ENERGY_DRAIN)
            self.active_effects.append(EnvironmentalEffect.HAPPINESS_REDUCTION)
            self.active_effects.append(EnvironmentalEffect.PRODUCTIVITY_REDUCTION)
            
        elif self.current_weather == WeatherType.FOG:
            self.active_effects.append(EnvironmentalEffect.SOLAR_REDUCTION)
            self.active_effects.append(EnvironmentalEffect.PRODUCTIVITY_REDUCTION)
            
        elif self.current_weather == WeatherType.SNOW:
            self.active_effects.append(EnvironmentalEffect.SOLAR_REDUCTION)
            self.active_effects.append(EnvironmentalEffect.HAPPINESS_REDUCTION)
            self.active_effects.append(EnvironmentalEffect.ENERGY_DRAIN)
            
    def get_solar_modifier(self) -> float:
        """Get solar power generation modifier"""
        modifier = 1.0
        
        if EnvironmentalEffect.SOLAR_BOOST in self.active_effects:
            modifier *= 1.5
        elif EnvironmentalEffect.SOLAR_REDUCTION in self.active_effects:
            modifier *= max(0.1, 1.0 - self.weather_intensity * 0.8)
            
        return modifier
        
    def get_productivity_modifier(self) -> float:
        """Get nano productivity modifier"""
        modifier = 1.0
        
        if EnvironmentalEffect.PRODUCTIVITY_BOOST in self.active_effects:
            modifier *= 1.2
        elif EnvironmentalEffect.PRODUCTIVITY_REDUCTION in self.active_effects:
            modifier *= max(0.5, 1.0 - self.weather_intensity * 0.4)
            
        return modifier
        
    def get_happiness_modifier(self) -> float:
        """Get nano happiness modifier"""
        modifier = 0.0
        
        if EnvironmentalEffect.HAPPINESS_BOOST in self.active_effects:
            modifier += 0.5
        elif EnvironmentalEffect.HAPPINESS_REDUCTION in self.active_effects:
            modifier -= self.weather_intensity * 1.0
            
        return modifier
        
    def get_energy_drain_rate(self) -> float:
        """Get additional energy drain rate"""
        if EnvironmentalEffect.ENERGY_DRAIN in self.active_effects:
            return self.weather_intensity * 0.1  # EU per hour
        return 0.0

class TimeSystem:
    """Manages game time, seasons, and day/night cycles"""
    
    def __init__(self):
        self.game_hour = 0  # 0-23
        self.game_day = 0
        self.game_month = 0  # 0-11
        self.game_year = 0
        
        self.time_accumulator = 0.0
        self.day_length = 24.0  # Real seconds per game day
        self.speed_multiplier = 1.0
        
        # Seasons (3 months each)
        self.seasons = [
            SeasonType.SPRING,  # Months 0-2
            SeasonType.SUMMER,  # Months 3-5
            SeasonType.AUTUMN,  # Months 6-8
            SeasonType.WINTER   # Months 9-11
        ]
        
        # Day/night cycle
        self.sunrise_hour = 6
        self.sunset_hour = 18
        
    def update(self, dt: float):
        """Update time system"""
        self.time_accumulator += dt * self.speed_multiplier
        
        # Check for hour advancement
        hours_per_second = 24.0 / self.day_length
        while self.time_accumulator >= 1.0 / hours_per_second:
            self.time_accumulator -= 1.0 / hours_per_second
            self.advance_hour()
            
    def advance_hour(self):
        """Advance game time by one hour"""
        self.game_hour += 1
        
        if self.game_hour >= 24:
            self.game_hour = 0
            self.game_day += 1
            
            # Check for month advancement (30 days per month)
            if self.game_day >= 30:
                self.game_day = 0
                self.game_month += 1
                
                # Check for year advancement
                if self.game_month >= 12:
                    self.game_month = 0
                    self.game_year += 1
                    
    def get_current_season(self) -> SeasonType:
        """Get current season based on month"""
        return self.seasons[self.game_month // 3]
        
    def is_daytime(self) -> bool:
        """Check if it's currently daytime"""
        return self.sunrise_hour <= self.game_hour < self.sunset_hour
        
    def get_sun_moon_position(self) -> float:
        """Get sun/moon position across sky (0.0 to 1.0)"""
        if self.is_daytime():
            # Sun position during day
            day_progress = (self.game_hour - self.sunrise_hour) / (self.sunset_hour - self.sunrise_hour)
            return max(0.0, min(1.0, day_progress))
        else:
            # Moon position during night
            if self.game_hour >= self.sunset_hour:
                night_hour = self.game_hour - self.sunset_hour
            else:
                night_hour = self.game_hour + (24 - self.sunset_hour)
            night_duration = 24 - (self.sunset_hour - self.sunrise_hour)
            return max(0.0, min(1.0, night_hour / night_duration))
            
    def get_light_level(self) -> float:
        """Get current light level (0.0 to 1.0)"""
        if self.is_daytime():
            # Full light during day
            return 1.0
        else:
            # Dim light during night
            return 0.2
            
    def get_time_string(self) -> str:
        """Get formatted time string"""
        return f"Year {self.game_year + 1}, Day {self.game_day + 1}, {self.game_hour:02d}:00"
        
    def get_season_string(self) -> str:
        """Get current season as string"""
        return self.get_current_season().value.title()

class EnvironmentalParticle:
    """Represents environmental particles (rain, snow, etc.)"""
    
    def __init__(self, x: float, y: float, particle_type: str):
        self.x = x
        self.y = y
        self.type = particle_type
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.life = 1.0
        self.size = 1.0
        self.color = (255, 255, 255)
        self.gravity = 0.0
        
        # Initialize based on type
        if particle_type == "rain":
            self.velocity_y = random.uniform(100, 200)
            self.velocity_x = random.uniform(-20, 20)
            self.life = random.uniform(3.0, 6.0)
            self.color = (100, 150, 255)
            self.size = random.uniform(1, 2)
            
        elif particle_type == "snow":
            self.velocity_y = random.uniform(20, 50)
            self.velocity_x = random.uniform(-10, 10)
            self.life = random.uniform(8.0, 15.0)
            self.color = (255, 255, 255)
            self.size = random.uniform(2, 4)
            self.gravity = 10.0
            
        elif particle_type == "fog":
            self.velocity_y = random.uniform(-5, 5)
            self.velocity_x = random.uniform(-30, 30)
            self.life = random.uniform(10.0, 20.0)
            self.color = (200, 200, 200)
            self.size = random.uniform(10, 20)
            
    def update(self, dt: float):
        """Update particle"""
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        self.velocity_y += self.gravity * dt
        self.life -= dt
        
        # Fade out over time
        if self.life < 1.0:
            alpha = max(0, self.life)
            self.color = (*self.color[:3], int(255 * alpha))

class ParticleSystem:
    """Manages environmental particle effects"""
    
    def __init__(self):
        self.particles = []
        self.spawn_timer = 0.0
        self.screen_width = WINDOW_WIDTH
        self.screen_height = WINDOW_HEIGHT
        
    def update(self, dt: float, weather: WeatherSystem, screen_width: int, screen_height: int):
        """Update particle system"""
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Update existing particles
        for particle in self.particles[:]:
            particle.update(dt)
            
            # Remove dead particles or those off screen
            if (particle.life <= 0 or 
                particle.x < -50 or particle.x > screen_width + 50 or
                particle.y < -50 or particle.y > screen_height + 50):
                self.particles.remove(particle)
                
        # Spawn new particles based on weather
        self.spawn_timer += dt
        spawn_rate = self.get_spawn_rate(weather)
        
        if spawn_rate > 0 and self.spawn_timer >= 1.0 / spawn_rate:
            self.spawn_timer = 0.0
            self.spawn_particle(weather)
            
    def get_spawn_rate(self, weather: WeatherSystem) -> float:
        """Get particle spawn rate based on weather"""
        if weather.current_weather == WeatherType.RAIN:
            return weather.weather_intensity * 50  # particles per second
        elif weather.current_weather == WeatherType.STORM:
            return weather.weather_intensity * 100
        elif weather.current_weather == WeatherType.SNOW:
            return weather.weather_intensity * 20
        elif weather.current_weather == WeatherType.FOG:
            return weather.weather_intensity * 5
        return 0.0
        
    def spawn_particle(self, weather: WeatherSystem):
        """Spawn a new particle"""
        x = random.uniform(-50, self.screen_width + 50)
        y = -50  # Start above screen
        
        if weather.current_weather == WeatherType.RAIN:
            particle = EnvironmentalParticle(x, y, "rain")
        elif weather.current_weather == WeatherType.STORM:
            particle = EnvironmentalParticle(x, y, "rain")
            particle.velocity_y *= 1.5  # Faster rain
            particle.velocity_x *= 2.0  # More wind
        elif weather.current_weather == WeatherType.SNOW:
            particle = EnvironmentalParticle(x, y, "snow")
        elif weather.current_weather == WeatherType.FOG:
            x = random.uniform(0, self.screen_width)
            y = random.uniform(0, self.screen_height)
            particle = EnvironmentalParticle(x, y, "fog")
        else:
            return
            
        self.particles.append(particle)
        
    def render(self, screen: pygame.Surface):
        """Render all particles"""
        for particle in self.particles:
            if particle.type == "fog":
                # Render fog as semi-transparent circles
                fog_surface = pygame.Surface((int(particle.size * 2), int(particle.size * 2)), pygame.SRCALPHA)
                pygame.draw.circle(fog_surface, (*particle.color[:3], 30), 
                                 (int(particle.size), int(particle.size)), int(particle.size))
                screen.blit(fog_surface, (int(particle.x - particle.size), int(particle.y - particle.size)))
            else:
                # Render rain/snow as small circles or lines
                if particle.type == "rain":
                    # Rain as lines
                    end_x = particle.x + particle.velocity_x * 0.1
                    end_y = particle.y + particle.velocity_y * 0.1
                    pygame.draw.line(screen, particle.color[:3], 
                                   (int(particle.x), int(particle.y)), 
                                   (int(end_x), int(end_y)), max(1, int(particle.size)))
                else:
                    # Snow as circles
                    pygame.draw.circle(screen, particle.color[:3], 
                                     (int(particle.x), int(particle.y)), max(1, int(particle.size)))

class EnvironmentManager:
    """Main environment manager that coordinates all environmental systems"""
    
    def __init__(self):
        self.time_system = TimeSystem()
        self.weather_system = WeatherSystem()
        self.particle_system = ParticleSystem()
        
        # Environmental modifiers
        self.temperature = 20.0  # Celsius
        self.humidity = 0.5  # 0.0 to 1.0
        self.air_pressure = 1013.25  # hPa
        
        # Events
        self.environmental_events = []
        self.event_check_timer = 0.0
        
        # Sync with game state time
        self.synced_with_game_time = False
        
    def sync_with_game_state(self, game_state):
        """Sync environment time with game state time"""
        self.time_system.game_hour = game_state.game_hour
        self.time_system.game_day = game_state.game_day
        self.time_system.game_month = game_state.game_month
        self.time_system.game_year = game_state.game_year
        self.synced_with_game_time = True
        
    def update(self, dt: float, screen_width: int, screen_height: int, game_state=None):
        """Update all environmental systems"""
        # Sync time with game state if provided
        if game_state and not self.synced_with_game_time:
            self.sync_with_game_state(game_state)
        elif game_state:
            # Keep in sync during updates
            self.time_system.game_hour = game_state.game_hour
            self.time_system.game_day = game_state.game_day
            self.time_system.game_month = game_state.game_month
            self.time_system.game_year = game_state.game_year
        
        # Update weather
        current_season = self.time_system.get_current_season()
        self.weather_system.update(dt, self.time_system.game_hour, current_season)
        
        # Update particles
        self.particle_system.update(dt, self.weather_system, screen_width, screen_height)
        
        # Update environmental conditions
        self.update_environmental_conditions()
        
        # Check for random events
        self.event_check_timer += dt
        if self.event_check_timer >= 60.0:  # Check every minute
            self.check_random_events()
            self.event_check_timer = 0.0
            
    def update_environmental_conditions(self):
        """Update temperature, humidity based on weather and season"""
        season = self.time_system.get_current_season()
        weather = self.weather_system.current_weather
        
        # Base temperature by season
        base_temps = {
            SeasonType.SPRING: 15.0,
            SeasonType.SUMMER: 25.0,
            SeasonType.AUTUMN: 10.0,
            SeasonType.WINTER: 0.0
        }
        
        self.temperature = base_temps[season]
        
        # Weather modifications
        if weather == WeatherType.STORM:
            self.temperature -= 5.0
            self.humidity = 0.9
        elif weather == WeatherType.RAIN:
            self.temperature -= 2.0
            self.humidity = 0.8
        elif weather == WeatherType.SNOW:
            self.temperature -= 10.0
            self.humidity = 0.7
        elif weather == WeatherType.FOG:
            self.humidity = 0.95
        elif weather == WeatherType.CLEAR:
            if self.time_system.is_daytime():
                self.temperature += 5.0
            self.humidity = 0.4
        else:  # CLOUDY
            self.humidity = 0.6
            
    def check_random_events(self):
        """Check for random environmental events"""
        # Very low chance of special events
        if random.random() < 0.01:  # 1% chance per minute
            event_types = ["solar_flare", "magnetic_storm", "meteor_shower", "aurora"]
            event = random.choice(event_types)
            self.trigger_environmental_event(event)
            
    def trigger_environmental_event(self, event_type: str):
        """Trigger a special environmental event"""
        event = {
            'type': event_type,
            'duration': random.uniform(30.0, 120.0),  # 30 seconds to 2 minutes
            'intensity': random.uniform(0.5, 1.0),
            'timer': 0.0
        }
        self.environmental_events.append(event)
        
    def apply_environmental_effects(self, game_state, dt: float):
        """Apply environmental effects to game state"""
        # Weather effects on resources
        solar_mod = self.weather_system.get_solar_modifier()
        productivity_mod = self.weather_system.get_productivity_modifier()
        happiness_mod = self.weather_system.get_happiness_modifier()
        energy_drain = self.weather_system.get_energy_drain_rate()
        
        # Apply solar effects to any solar generators
        if solar_mod != 1.0:
            # Future: Apply to solar power generation
            pass
            
        # Apply energy drain
        if energy_drain > 0:
            game_state.resources.surge_capacitor = max(0, 
                game_state.resources.surge_capacitor - energy_drain * dt / 3600.0)
            
        # Apply effects to Nanos - only affect those outside buildings during bad weather
        for nano in game_state.nanos.values():
            # Productivity effects - only if working and not in building
            if hasattr(nano, 'productivity_modifier'):
                nano.productivity_modifier = productivity_mod
                
            # Happiness effects - reduced for those in shelter during bad weather
            if happiness_mod != 0:
                # Nanos inside buildings get protection from bad weather
                weather_protection = 0.5 if nano.inside_building and happiness_mod < 0 else 1.0
                adjusted_happiness_mod = happiness_mod * weather_protection
                nano.happy = max(0, min(100, nano.happy + adjusted_happiness_mod * dt))
                
        # Handle special events
        for event in self.environmental_events[:]:
            event['timer'] += dt
            
            if event['type'] == "solar_flare":
                # Boost energy generation
                game_state.resources.work_power *= (1.0 + event['intensity'] * 0.5)
            elif event['type'] == "magnetic_storm":
                # Drain energy
                drain = event['intensity'] * 0.5 * dt
                game_state.resources.surge_capacitor = max(0, 
                    game_state.resources.surge_capacitor - drain)
            elif event['type'] == "meteor_shower":
                # Random resource bonus
                if random.random() < 0.1:  # 10% chance per second
                    game_state.resources.add_eu(event['intensity'] * 0.1)
                    
            # Remove expired events
            if event['timer'] >= event['duration']:
                self.environmental_events.remove(event)
                
    def get_sky_color(self) -> Tuple[int, int, int]:
        """Get current sky color based on time and weather"""
        is_day = self.time_system.is_daytime()
        weather = self.weather_system.current_weather
        
        if is_day:
            if weather == WeatherType.CLEAR:
                return (135, 206, 235)  # Sky blue
            elif weather == WeatherType.CLOUDY:
                return (100, 150, 200)  # Cloudy blue
            elif weather == WeatherType.RAIN or weather == WeatherType.STORM:
                return (70, 100, 150)   # Storm blue
            elif weather == WeatherType.FOG:
                return (150, 150, 150)  # Grey
            elif weather == WeatherType.SNOW:
                return (200, 200, 220)  # Snowy grey
        else:
            # Night colors
            if weather == WeatherType.CLEAR:
                return (25, 25, 112)    # Midnight blue
            else:
                return (15, 15, 60)     # Dark night
                
        return (50, 50, 50)  # Default
        
    def get_ambient_light(self) -> float:
        """Get ambient light level"""
        base_light = self.time_system.get_light_level()
        
        # Weather modifications
        weather = self.weather_system.current_weather
        if weather == WeatherType.STORM:
            base_light *= 0.6
        elif weather == WeatherType.RAIN:
            base_light *= 0.8
        elif weather == WeatherType.FOG:
            base_light *= 0.7
        elif weather == WeatherType.SNOW:
            base_light *= 0.9
            
        return max(0.1, min(1.0, base_light))
        
    def render_environmental_overlay(self, screen: pygame.Surface):
        """Render environmental overlay effects"""
        # Render particles
        self.particle_system.render(screen)
        
        # Render ambient lighting overlay
        light_level = self.get_ambient_light()
        if light_level < 1.0:
            darkness = int((1.0 - light_level) * 100)
            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, darkness))
            screen.blit(overlay, (0, 0))
            
    def get_environment_info(self) -> Dict[str, str]:
        """Get formatted environment information for UI"""
        return {
            'time': self.time_system.get_time_string(),
            'season': self.time_system.get_season_string(),
            'weather': self.weather_system.current_weather.value.title(),
            'temperature': f"{self.temperature:.1f}°C",
            'humidity': f"{self.humidity * 100:.0f}%"
        }

#EOF ENVIRONMENT.PY
