import time
import socket
import os
import hashlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

HOST = 'localhost'
PORT  = 8111

class MyEventHandler(FileSystemEventHandler):
    def __init__(self) -> None:
        super().__init__()
        self.track_file = {}

    def ignoreFileType(self, filename):
        file_type = os.path.splitext(filename)[1] #tuple (filename, type)
        ignore_types_list = ['.tmp', '.TMP']
        if file_type in ignore_types_list:
            return True
        if filename.startswith('.') or filename.startswith('~'):
            return True
        return False

    def sendToEncrypt(self, path):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((HOST, PORT))
                source = path
                destination = path+'.enc'
                message = f"encrypt,{source},{destination}"
                client_socket.sendall(message.encode())
        except Exception as ex:
            print(f'Cannot connect to server, {ex}')


    def generateHash(self, path):
        try:
            with open(path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            return file_hash
        except Exception as ex:
            print(f'Exception generating hash, {ex}')
            return None

    def on_created(self, event):
        print("Created", self.track_file)

        basename = os.path.basename(event.src_path)
        file_type = os.path.splitext(basename) #tuple (filename, type)
        folder_path = os.path.split(event.src_path)

        if self.ignoreFileType(basename):
            return

        if file_type[1] == '.enc':
            print('created new .enc files')
            return
                
        if not os.path.exists(event.src_path+'.enc'):
            print(f"new  file created: {event.src_path}")
            self.sendToEncrypt(event.src_path)
            return

        if basename not in self.track_file.keys():
            print("incomming new file update")
            hash = self.generateHash(event.src_path)
            self.track_file[basename] = hash
            return

    def on_modified(self, event):
        print("Modified", self.track_file)
        basename = os.path.basename(event.src_path)
        file_type = os.path.splitext(basename) #tuple (filename, type)
        folder_path = os.path.split(event.src_path)

        if self.ignoreFileType(basename):
            return
        if file_type[1] == '.enc':
            print('modified new .enc files')
            return

        if basename not in self.track_file.keys():
            return
        
        hash = self.generateHash(event.src_path)
        
        if self.track_file[basename] != hash:
            print(f"Modified: {event.src_path}")
            self.sendToEncrypt(event.src_path)

    def on_deleted(self, event):
        print(f"Deleted: {event.src_path}")


if __name__ == "__main__":
    event_handler = MyEventHandler()
    observer = Observer()

    # Set the directory to monitor
    directory = r"C:\Users\WatchFolder"

    # Schedule the event handler and directory for monitoring
    observer.schedule(event_handler, directory, recursive=True)

    # Start the observer
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
