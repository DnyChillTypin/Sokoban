# tween.py

# ==========================================
# EASING FUNCTIONS
# 't' represents the progress from 0.0 to 1.0
# ==========================================

def linear(t):
    return t

def ease_out_quad(t):
    return 1 - (1 - t) * (1 - t)

def ease_out_bounce(t):
    if t < 1 / 2.75:
        return 7.5625 * t * t
    elif t < 2 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    elif t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    else:
        t -= 2.625 / 2.75
        return 7.5625 * t * t + 0.984375


# ==========================================
# TWEEN & MANAGER CLASSES
# ==========================================

class Tween:
    """Handles a single animation from a start value to an end value over time."""
    
    def __init__(self, target, attribute, end_val, duration, easing_func):
        self.target = target
        self.attribute = attribute
        
        # Grab the initial value dynamically
        self.start_val = getattr(self.target, self.attribute)
        self.end_val = end_val
        
        # We track the current value as a float internally!
        # Pygame Rects truncate decimals to ints immediately. If we don't track 
        # the float separately, slow animations will permanently freeze.
        self.current_float_val = float(self.start_val)
        
        self.duration = duration
        self.easing_func = easing_func
        self.elapsed = 0.0

    def update(self, dt):
        """Advances the animation by delta time. Returns True if finished."""
        self.elapsed += dt
        
        # Calculate normalized progress (0.0 to 1.0)
        progress = min(self.elapsed / self.duration, 1.0)
        
        # Apply the easing math
        eased_progress = self.easing_func(progress)
        
        # Calculate the new value
        change = self.end_val - self.start_val
        self.current_float_val = self.start_val + (change * eased_progress)
        
        # Apply it to the target object (casting to int handles Pygame Rects safely)
        setattr(self.target, self.attribute, int(self.current_float_val))
        
        # If progress is 1.0 or greater, the tween is done
        return progress >= 1.0


class TweenManager:
    """Centralized manager to update all active animations safely."""
    
    def __init__(self):
        self.tweens = []

    def add_tween(self, target, attribute, end_val, duration, easing_func=ease_out_quad):
        """Creates a new tween and adds it to the active list."""
        new_tween = Tween(target, attribute, end_val, duration, easing_func)
        self.tweens.append(new_tween)

    def update(self, dt):
        """Called once per frame to step all active animations forward."""
        if not self.tweens:
            return
            
        # Iterate backwards so we can safely remove finished tweens without skipping elements
        for i in range(len(self.tweens) - 1, -1, -1):
            is_finished = self.tweens[i].update(dt)
            if is_finished:
                self.tweens.pop(i)