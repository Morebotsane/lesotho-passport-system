# tests/test_rate_limit.py
import requests
import time

# Use an API endpoint instead of /health
url = "http://localhost:8000/api/v1/passport-applications/track/TEST123"

print("Testing rate limiting with 25 rapid requests...")
for i in range(1, 26):
    try:
        response = requests.get(url)
        remaining = response.headers.get('X-RateLimit-Remaining', 'N/A')
        limit = response.headers.get('X-RateLimit-Limit', 'N/A')
        print(f"Request {i}: Status {response.status_code} - Limit: {limit}, Remaining: {remaining}")
        
        if response.status_code == 429:
            print(f"  RATE LIMITED! Retry after: {response.headers.get('Retry-After', 'N/A')} seconds")
            
    except Exception as e:
        print(f"Request {i}: Error - {e}")
    
    time.sleep(0.1)