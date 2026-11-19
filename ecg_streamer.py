import time
import eventlet
from threading import Thread
from detector import ECGDetector

class ECGStreamer:
    def __init__(self, socketio, detector, notification_handler=None):
        self.socketio = socketio
        self.detector = detector
        self.notification_handler = notification_handler
        self.is_streaming = False
        self.current_idx = 0
        self.chunk_size = 128
        self.stream_thread = None
        
    def start_streaming(self):
        if self.is_streaming:
            return
        
        self.is_streaming = True
        self.current_idx = 0
        self.stream_thread = Thread(target=self._stream_loop)
        self.stream_thread.daemon = True
        self.stream_thread.start()
        print("ECG streaming started")
    
    def stop_streaming(self):
        self.is_streaming = False
        if self.stream_thread:
            self.stream_thread.join(timeout=2)
        print("ECG streaming stopped")
    
    def _send_notification_async(self, alert_type, alert_bpm):
        try:
            self.notification_handler.send_alert(alert_type, alert_bpm)
        except Exception as e:
            print(f"Error sending notification for {alert_type}: {e}")
    
    def _stream_loop(self):
        signal_length = self.detector.get_signal_length()
        
        while self.is_streaming and self.current_idx < signal_length:
            chunk_samples = self.detector.get_chunk(self.current_idx, self.chunk_size)
            
            peaks_in_chunk = self.detector.get_peaks_in_range(
                self.current_idx, 
                self.current_idx + len(chunk_samples)
            )
            
            bpm = self.detector.calculate_bpm(self.current_idx + len(chunk_samples))
            
            current_time = (self.current_idx + len(chunk_samples)) / self.detector.fs
            alerts, alert_types = self.detector.check_alerts(bpm, current_time)
            
            clinical_suggestions = []
            if self.notification_handler and alert_types:
                for alert_type, alert_bpm in alert_types:
                    eventlet.spawn_n(self._send_notification_async, alert_type, alert_bpm)
                    clinical_info = self.notification_handler.get_clinical_suggestions(alert_type, alert_bpm)
                    if clinical_info:
                        clinical_suggestions.append(clinical_info)
            
            payload = {
                't0': self.current_idx / self.detector.fs,
                'fs': self.detector.fs,
                'samples': chunk_samples,
                'peaks': peaks_in_chunk,
                'bpm': bpm,
                'alerts': alerts,
                'clinical_suggestions': clinical_suggestions
            }
            
            self.socketio.emit('ecg_chunk', payload)
            
            self.current_idx += len(chunk_samples)
            
            sleep_time = len(chunk_samples) / self.detector.fs
            time.sleep(sleep_time)
        
        if self.current_idx >= signal_length:
            print("ECG stream completed")
            self.socketio.emit('stream_complete', {'message': 'ECG recording complete'})
            self.is_streaming = False
