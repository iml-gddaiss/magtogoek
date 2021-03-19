# Description
This will monitor the UDP port for any data (ADCP DVL).

This will monitor UDP port 257, the default port on the ADCP.  You can change the port in the source code.
```python
UDP_PORT = 257
```

# Create EXE
```bash
pyinstaller udp_receive.py
```