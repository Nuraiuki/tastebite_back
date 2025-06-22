import os
import subprocess

# Get the DATABASE_URL from Render environment (you need to get this from your Render dashboard)
# For security reasons, I'm using a placeholder. 
# PLEASE REPLACE THIS WITH YOUR ACTUAL DATABASE_URL
DATABASE_URL = "postgresql://tastebite_sql_user:X8yEKIh4dtKHXS0HLaCKUMChhDZ0YEOR@dpg-d1bej2adbo4c73cergm0-a/tastebite_sql" 

# Set the environment variable for the script
env = os.environ.copy()
env["DATABASE_URL"] = DATABASE_URL
env["FLASK_APP"] = "wsgi:app" # Add this to ensure correct app context

# Activate venv and run the script
command = [
    "source", "venv/bin/activate", "&&",
    "python3", "make_admin.py", "n@gmail.com"
]

# Since 'source' is a shell builtin, we need to run it in a shell
subprocess.run(" ".join(command), shell=True, env=env, executable="/bin/zsh") 