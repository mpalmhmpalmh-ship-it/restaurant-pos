from flask import Flask, redirect

app = Flask(__name__)

@app.route("/")
def home():
    return "POS is running ✅"

@app.route("/pos")
def pos():
    return "POS PAGE"

if __name__ == "__main__":
    app.run()
