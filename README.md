# poison.py
Fast tool to search log's for LFI vulnerabilities, and automatic escalation to shell

## Exploitation:
![Preview](https://github.com/user-attachments/assets/8d658876-79d6-41f1-9456-91681be9782e)



## Example usage:
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
# ToDo list:
-   [x] Add the function with command execution
-   [x] Add the support of wordlist's
-   [ ] Add different injection endpoints (Headers)
-   [ ] Interactive shell 
-   [ ] Add the function for RFI

# FOR EDUCATIONAL PURPOSES ONLY!
Usage of poison.py for attacking targets without prior mutual consent is illegal. It is the end user's responsibility to obey all applicable local, state and federal laws. Author assume no liability and are not responsible for any misuse or damage caused by this program
