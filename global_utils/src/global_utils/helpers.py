import re
from datetime import datetime, timedelta
from DataPipelineHub.backend.shared import logger

def parse_date_range_to_days(date_range: str) -> int:
    """
    Parse date range string into number of days.
    Supports formats like: "7d", "30d", "1m", "1y"
    
    Args:
        date_range: String like "7d", "30d", etc.
        
    Returns:
        Number of days to go back
    """
    if not date_range:
        return 30  # Default to 30 days
        
    date_range = date_range.lower().strip()
    
    # Handle compact formats like "7d", "30d", "1m", "1y"
    compact_match = re.search(r'(\d+)([dmyh])', date_range)
    if compact_match:
        number = int(compact_match.group(1))
        unit = compact_match.group(2)
        
        if unit == 'd':
            return number
        elif unit == 'm':
            return number * 30
        elif unit == 'y':
            return number * 365
        elif unit == 'h':
            return max(1, number // 24)  # Convert hours to days, minimum 1 day
    
    logger.warning(f"Unable to parse date range '{date_range}', defaulting to 30 days")
    return 30  # Default fallback

def calculate_date_range(date_range: str) -> tuple[datetime, datetime]:
    """
    Calculate start and end datetime objects based on date range.
    
    Args:
        date_range: String like "7d", "30d", etc.
        
    Returns:
        Tuple of (start_datetime, end_datetime)
        
    Example:
        If today is 2025-01-05 and date_range is "7d":
        - start_datetime: 2024-12-29 00:00:00 (7 days ago at midnight)
        - end_datetime: 2025-01-05 14:30:15 (current datetime)
    """
    # Current datetime (end of range)
    end_datetime = datetime.now()
    
    # Calculate how many days back to go
    if not date_range:
        days_back = 30
        logger.info(f"No date range specified, defaulting to {days_back} days back")
    else:
        days_back = parse_date_range_to_days(date_range)
        logger.info(f"Date range '{date_range}' parsed as {days_back} days back")
    
    # Calculate start date (X days ago at midnight)
    start_date = (end_datetime - timedelta(days=days_back)).date()
    start_datetime = datetime.combine(start_date, datetime.min.time())
    
    # Log human-readable dates for verification
    logger.info(f"📅 Calculated date range:")
    logger.info(f"   Start: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')} ({days_back} days ago)")
    logger.info(f"   End:   {end_datetime.strftime('%Y-%m-%d %H:%M:%S')} (now)")
    logger.info(f"   Range: {start_datetime.strftime('%Y-%m-%d')} to {end_datetime.strftime('%Y-%m-%d')}")
    
    return start_datetime, end_datetime
