from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "<h1>OQAS is running! 🚀 Congratulations IB CODE SWEET</h1>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

