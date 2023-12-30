from website import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='192.168.0.1', port=80, debug=True)
    # app.run(debug=True)
    