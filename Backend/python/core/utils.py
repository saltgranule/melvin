import re
import datetime

def parse_duration(duration_str: str) -> datetime.timedelta:
    """Parses a duration string like '1h', '2d', '1w' into a timedelta object."""
    if not duration_str:
        return None
    
    regex = re.compile(r"(\d+)\s*([smhdw])")
    matches = regex.findall(duration_str.lower())
    
    if not matches:
        return None
    
    total_seconds = 0
    units = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        'w': 604800
    }
    
    for amount, unit in matches:
        total_seconds += int(amount) * units[unit]
        
    return datetime.timedelta(seconds=total_seconds)
