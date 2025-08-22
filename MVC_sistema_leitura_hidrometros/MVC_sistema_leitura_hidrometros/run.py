from app import app, socketio

if __name__ == "__main__":
    # Usa eventlet/gevent automático do Flask-SocketIO se instalado; caso contrário fallback
    socketio.run(app, host='0.0.0.0', port=5000)
