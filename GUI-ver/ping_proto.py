# python3 test.py http://www.gstatic.com/generate_204 127.0.0.1:1080
import urllib.request
import urllib.error
import argparse
import sys
import time

def test_proxy(url, proxy_url, username=None, password=None):
    # Set the proxy handler with the provided proxy URL
    proxy_handler = urllib.request.ProxyHandler({'http': proxy_url})
    
    # If username and password are provided, set up basic authentication
    if username and password:
        password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, proxy_url, username, password)
        auth_handler = urllib.request.ProxyBasicAuthHandler(password_mgr)
        opener = urllib.request.build_opener(proxy_handler, auth_handler)
    else:
        # If no authentication is needed, just use the proxy handler
        opener = urllib.request.build_opener(proxy_handler)
    
    # Install the opener as the default opener for urllib requests
    urllib.request.install_opener(opener)
    
    try:
        # Start measuring the time before making the request
        start_time = time.time()  
        
        # Attempt to open the provided URL with a 10-second timeout
        with urllib.request.urlopen(url, timeout=10) as response:
            response.read(1)  # Read a small portion of the response to ensure the request goes through
        
        # Measure the time after the response is received
        end_time = time.time()  
        
        # Calculate the latency (ping) in seconds
        latency = end_time - start_time  
        
        # Return success and the latency in seconds
        return True, f"Success: Connected through proxy. Response time: {latency:.4f} seconds."
    
    except urllib.error.URLError as e:
        # Return failure and the reason for the URLError (e.g., connection issues)
        return False, f"Error: {e.reason}"
    except Exception as e:
        # Handle unexpected errors and return the error message
        return False, f"Unexpected error: {str(e)}"

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="HTTP Proxy Tester")
    
    # Required argument: URL to test (e.g., http://example.com)
    parser.add_argument("url", help="URL to test (e.g., http://example.com)")
    
    # Required argument: Proxy URL to use (e.g., http://proxy.example.com:8080)
    parser.add_argument("proxy", help="Proxy URL (e.g., http://proxy.example.com:8080)")
    
    # Optional argument: Username for proxy authentication (if needed)
    parser.add_argument("-u", "--username", help="Username for proxy authentication (optional)")
    
    # Optional argument: Password for proxy authentication (if needed)
    parser.add_argument("-p", "--password", help="Password for proxy authentication (optional)")
    
    # Parse the command-line arguments
    args = parser.parse_args()
    
    # Test the proxy using the provided URL and proxy URL, and optional username/password
    success, message = test_proxy(args.url, args.proxy, args.username, args.password)
    
    # Print the result message
    print(message)
    
    # Exit the program with status 0 if successful, otherwise 1
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    # Start the main function if the script is being run directly
    main()
