from flask import Flask, render_template, redirect, url_for
import subprocess
import sys
import os
import signal

app = Flask(__name__)

GAME_PROCESS = None

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
MAIN_FILE = os.path.join(PROJECT_ROOT, "main.py")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start")
def start_game():
    global GAME_PROCESS

    if GAME_PROCESS is None or GAME_PROCESS.poll() is not None:
        GAME_PROCESS = subprocess.Popen(
            [sys.executable, MAIN_FILE],
            cwd=PROJECT_ROOT
        )

    return redirect(url_for("index"))


@app.route("/stop")
def stop_game():
    global GAME_PROCESS

    if GAME_PROCESS and GAME_PROCESS.poll() is None:
        GAME_PROCESS.terminate()
        GAME_PROCESS = None

    return redirect(url_for("index"))


@app.route("/restart")
def restart_game():
    global GAME_PROCESS

    if GAME_PROCESS and GAME_PROCESS.poll() is None:
        GAME_PROCESS.terminate()

    GAME_PROCESS = subprocess.Popen(
        [sys.executable, MAIN_FILE],
        cwd=PROJECT_ROOT
    )

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
