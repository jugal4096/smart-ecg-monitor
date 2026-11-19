import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, send_from_directory, request, jsonify
from flask_socketio import SocketIO, emit
from detector import ECGDetector
from ecg_streamer import ECGStreamer
from notification_handler import NotificationHandler

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'ecg-monitor-secret-key'

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

detector = ECGDetector()
notification_handler = NotificationHandler()
streamer = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('start_stream')
def handle_start_stream():
    global streamer
    
    if streamer and streamer.is_streaming:
        emit('error', {'message': 'Stream already running'})
        return
    
    try:
        detector.load_record('100', 'mitdb')
        
        streamer = ECGStreamer(socketio, detector, notification_handler)
        streamer.start_streaming()
        
        emit('stream_started', {
            'message': 'ECG stream started',
            'fs': detector.fs,
            'total_samples': detector.get_signal_length()
        })
    except Exception as e:
        print(f"Error starting stream: {e}")
        emit('error', {'message': f'Error starting stream: {str(e)}'})

@socketio.on('stop_stream')
def handle_stop_stream():
    global streamer
    
    if streamer:
        streamer.stop_streaming()
        emit('stream_stopped', {'message': 'ECG stream stopped'})

@socketio.on('set_notification_config')
def handle_set_notification_config(data):
    try:
        notification_handler.set_config(data)
        emit('notification_config_updated', {
            'status': 'success',
            'config': notification_handler.notification_config
        })
        print(f"Notification config updated: {data}")
    except Exception as e:
        print(f"Error updating notification config: {e}")
        emit('error', {'message': f'Error updating config: {str(e)}'})

@socketio.on('get_notification_config')
def handle_get_notification_config():
    emit('notification_config', notification_handler.notification_config)

@app.route('/api/clinical-suggestions/<alert_type>/<int:bpm>')
def get_clinical_suggestions(alert_type, bpm):
    suggestions = notification_handler.get_clinical_suggestions(alert_type, bpm)
    return jsonify(suggestions)

if __name__ == '__main__':
    print("Starting ECG Monitor Server...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
