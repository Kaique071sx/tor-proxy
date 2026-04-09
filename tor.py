import time
import requests
from stem import Signal
from stem.control import Controller
from colorama import init, Fore, Style
import datetime
import argparse

init(autoreset=True)  # Initialize colorama

def get_current_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json', proxies={'https': 'socks5://127.0.0.1:9050'})
        return response.json()['ip']
    except Exception:
        return "Unknown"

def change_tor_ip(counter):
    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
            new_ip = get_current_ip()
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{Fore.GREEN}[{current_time}] New Tor circuit created (#{counter})")
            print(f"{Fore.CYAN}New IP: {Style.BRIGHT}{new_ip}")
            return True
    except Exception as e:
        print(f"{Fore.RED}An error occurred: {e}")
        return False

def main(interval):
    print(f"{Fore.YELLOW}{Style.BRIGHT}Starting Tor IP rotation every {interval} seconds. Press Ctrl+C to stop.")
    counter = 0
    try:
        while True:
            if change_tor_ip(counter + 1):
                counter += 1
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Tor IP rotation stopped.")
        print(f"{Fore.MAGENTA}Total IP rotations: {Style.BRIGHT}{counter}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rotate Tor IP address at specified intervals.")
    parser.add_argument("interval", type=int, nargs="?", default=3, 
                        help="Number of seconds between IP rotations (minimum 3)")
    args = parser.parse_args()

    if args.interval < 3:
        print(f"{Fore.RED}Error: Interval must be at least 3 seconds.")
        exit(1)

    main(args.interval)