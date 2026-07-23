import os
from flask import Flask
app = Flask(__name__, static_folder='../frontend', static_url_path='')
print(f"App root path: {app.root_path}")
print(f"Static folder: {app.static_folder}")
print(f"Exists? {os.path.exists(app.static_folder)}")
print(f"Full path: {os.path.abspath(app.static_folder)}")
