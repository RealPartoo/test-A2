from project import create_app

app = create_app()

if __name__ == "__main__":
    # debug=True is handy while developing
    app.run(debug=True)
