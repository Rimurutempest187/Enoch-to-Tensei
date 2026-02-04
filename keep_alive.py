from flask import Flask
from threading import Thread

app_web = Flask("")

@app_web.route("/")
def home():
    return "Bot Alive!"

def run_web():
    app_web.run("0.0.0.0", 8080)

def keep_alive():
    Thread(target=run_web).start()
