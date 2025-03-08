import subprocess
import json
import time
import os

# Initial settings
XRAY_PATH = "./core/linux/xray"  # Path to the xray executable
SERVER = "127.0.0.1:10085"  # API server address
CHECK_INTERVAL = 5  # Time interval between checks (in seconds)

# Function to convert bytes to a human-readable unit (KB, MB, GB)
def format_bytes(bytes_size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0

# Function to get traffic stats from Xray
def get_traffic_stats(stat_name):
    try:
        # Execute the xray api stats command
        result = subprocess.run(
            [XRAY_PATH, "api", "stats", f"--server={SERVER}", f"-name={stat_name}"],
            capture_output=True,
            text=True
        )
        # Check if the output is successful
        if result.returncode == 0:
            data = json.loads(result.stdout)
            value = data.get("stat", {}).get("value", 0)
            return value
        else:
            print(f"Error getting {stat_name}: {result.stderr}")
            return 0
    except Exception as e:
        print(f"Error: {e}")
        return 0

# Main loop for monitoring
def main():
    # Ensure the xray executable exists
    if not os.path.exists(XRAY_PATH):
        print(f"File {XRAY_PATH} not found. Please provide the correct path.")
        return

    print("Starting traffic monitoring... (Press Ctrl+C to exit)")
    print("-" * 50)

    while True:
        # Get upload and download stats
        uplink = get_traffic_stats("outbound>>>proxy>>>traffic>>>uplink")
        downlink = get_traffic_stats("outbound>>>proxy>>>traffic>>>downlink")

        # Convert to readable units
        uplink_str = format_bytes(uplink)
        downlink_str = format_bytes(downlink)

        # Display the output
        os.system("clear")  # Clear the terminal (for Linux/Mac) - use "cls" for Windows
        print(f"📤 Upload (Uplink): {uplink_str}")
        print(f"📥 Download (Downlink): {downlink_str}")
        print(f"Next update: {CHECK_INTERVAL} seconds")

        # Wait until the next check
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nMonitoring stopped. Goodbye!")