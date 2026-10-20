# Lab1: Secure REST API & CVE Vulnerability Reproduction
Name: Yu Jiawen
Student ID: 23320304

## Selected CVE: CVE-2016-3088 Apache ActiveMQ Arbitrary File Write Vulnerability
### Vulnerability description
Apache ActiveMQ contains an unauthenticated file server endpoint `/fileserver`. Attackers can send HTTP PUT requests to upload arbitrary files to the server. If attackers upload malicious JSP webshell files, they can achieve remote code execution on the host.

### Reproduction steps
1. Start the vulnerable environment with `docker-compose up -d`
2. Use Postman to send PUT request to `http://127.0.0.1:8161/fileserver/test.txt`, the request body contains custom text.
3. The server returns HTTP 204 No Content. The uploaded file can be directly accessed via browser, which proves the arbitrary file write vulnerability exists.
(Screenshot: Vulnerability reproduction, Postman 204 response + browser preview of uploaded file)

### Root-cause analysis
The fileserver web application is enabled in jetty.xml by default without authentication. It accepts HTTP PUT requests and writes user-controllable content directly to the server disk. There is no filter to block executable script files.

### Applied Fix
Edit jetty.xml configuration file and comment out the entire fileserver webapp configuration block. After restarting ActiveMQ service, the `/fileserver` web endpoint will be removed.

### Verification of the fix
After applying the patch:
1. Send the same PUT upload request to `/fileserver` again. The server returns HTTP 404 Not Found. The file upload function is disabled.
2. Regression test: Access ActiveMQ homepage `http://127.0.0.1:8161`. The web management page works normally, and the core message queue service is unaffected.
