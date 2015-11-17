# P2PCentralizedIndex
Peer-to-Peer with Centralized Index (P2P-CI) System for Downloading

# ToDo
- Support for passing parameters like MSS (Maximum segment size), N (window size), P (packet drop probability) through command line from the client. Currently it is hardcoded in the files.
- For large files, the FTP transfer is not happening properly and there is some repeatition of data received on the receiver end. Should debug and look into the issue.
- Currently only text file transfer is supported. Was getting "invalid characters" exception when reading pdf files. 
- Setup the VM's in VMWare Workstation to test the project.
- Report
