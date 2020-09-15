from api import app

if __name__ == "__main__":
    from api import suggestions
    app.run(host='0.0.0.0', port=5000, debug=True)