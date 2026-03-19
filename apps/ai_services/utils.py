import time
from .models import APILog

def log_api_call(user, service_name, endpoint_used, start_time, tokens_used=0, successful=True):
    """
    Calculates latency and saves a standardized API Log entry.
    """
    # Calculate how long the API call took
    latency = time.time() - start_time
    
    # Create and return the log
    return APILog.objects.create(
        user=user,
        service_name=service_name,
        endpoint_used=endpoint_used,
        tokens_used=tokens_used,
        latency_seconds=round(latency, 3), # Round to 3 decimal places for clean DB storage
        successful=successful
    ) 