import numpy as np
import wfdb
from wfdb.processing import gqrs_detect

class ECGDetector:
    def __init__(self):
        self.record = None
        self.signal = None
        self.fs = None
        self.qrs_indices = None
        self.rr_intervals = []
        self.last_bpm = None
        self.bpm_history = []
        
    def load_record(self, record_name='100', db='mitdb'):
        self.rr_intervals = []
        self.last_bpm = None
        self.bpm_history = []
        
        print(f"Loading ECG record {record_name} from {db} database...")
        self.record = wfdb.rdrecord(record_name, pn_dir=db)
        self.signal = self.record.p_signal[:, 0]
        self.fs = self.record.fs
        print(f"Loaded {len(self.signal)} samples at {self.fs} Hz")
        
        print("Detecting QRS complexes...")
        self.qrs_indices = gqrs_detect(self.signal, fs=self.fs)
        print(f"Detected {len(self.qrs_indices)} R-peaks")
        
        self._calculate_rr_intervals()
        
    def _calculate_rr_intervals(self):
        if len(self.qrs_indices) > 1:
            self.rr_intervals = np.diff(self.qrs_indices) / self.fs
    
    def get_peaks_in_range(self, start_idx, end_idx):
        peaks_in_range = self.qrs_indices[
            (self.qrs_indices >= start_idx) & (self.qrs_indices < end_idx)
        ]
        relative_peaks = peaks_in_range - start_idx
        return relative_peaks.tolist()
    
    def calculate_bpm(self, current_idx):
        recent_peaks = self.qrs_indices[self.qrs_indices <= current_idx]
        
        if len(recent_peaks) < 2:
            return None
        
        last_two_peaks = recent_peaks[-2:]
        rr_interval = (last_two_peaks[1] - last_two_peaks[0]) / self.fs
        
        if rr_interval > 0:
            bpm = 60.0 / rr_interval
            self.last_bpm = bpm
            self.bpm_history.append((current_idx / self.fs, bpm))
            return round(bpm, 1)
        
        return None
    
    def check_alerts(self, bpm, current_time):
        alerts = []
        alert_types = []
        
        if bpm is None:
            return alerts, alert_types
        
        if bpm < 60:
            alerts.append(f"⚠️ Bradycardia detected: {bpm} BPM")
            alert_types.append(('bradycardia', bpm))
        elif bpm > 100:
            alerts.append(f"⚠️ Tachycardia detected: {bpm} BPM")
            alert_types.append(('tachycardia', bpm))
        
        if len(self.bpm_history) > 1:
            recent_history = [
                (t, b) for t, b in self.bpm_history 
                if current_time - t <= 10
            ]
            
            if len(recent_history) >= 2:
                bpm_values = [b for _, b in recent_history]
                max_change = max(bpm_values) - min(bpm_values)
                
                if max_change > 20:
                    alerts.append(f"⚠️ Sudden BPM change: {round(max_change, 1)} BPM in 10 seconds")
                    alert_types.append(('sudden_change', bpm))
        
        return alerts, alert_types
    
    def get_signal_length(self):
        return len(self.signal) if self.signal is not None else 0
    
    def get_chunk(self, start_idx, chunk_size):
        end_idx = min(start_idx + chunk_size, len(self.signal))
        return self.signal[start_idx:end_idx].tolist()
