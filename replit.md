# Real-Time ECG Monitor

## Overview
A web-based real-time ECG (electrocardiogram) monitoring application that visualizes cardiac activity using authentic medical data from the MIT-BIH Arrhythmia Database. The application provides live ECG waveform visualization, automatic heart rate calculation, R-peak detection, and clinical alert detection for various cardiac conditions.

## Project Architecture

### Backend (Python)
- **Flask**: Web server framework
- **Flask-SocketIO**: WebSocket support for real-time data streaming
- **eventlet**: Asynchronous networking library for concurrent connections
- **wfdb**: PhysioNet WFDB library for ECG database access
- **numpy & scipy**: Signal processing and numerical operations

### Frontend (JavaScript)
- **Chart.js**: Real-time ECG waveform visualization
- **Socket.IO Client**: WebSocket client for live data streaming
- **Vanilla JavaScript**: No framework dependencies for simplicity

## Project Structure
```
/
├── app.py                  # Main Flask application and WebSocket handlers
├── detector.py            # ECG signal processing and R-peak detection
├── ecg_streamer.py        # Background streaming service
├── notification_handler.py # Email/SMS notification system
├── templates/
│   └── index.html         # Main web interface
├── static/
│   ├── script.js          # Frontend logic and Chart.js integration
│   └── style.css          # Modern medical UI styling
└── replit.md             # This file
```

## Key Features

### 1. Real-Time ECG Streaming
- Streams ECG data from MIT-BIH Arrhythmia Database Record 100
- 128 samples per chunk at 360 Hz sampling rate
- Automatic real-time synchronization with medical-grade timing

### 2. R-Peak Detection
- Uses GQRS (General QRS) detector from wfdb.processing
- Visual markers on detected R-peaks (red dots)
- Accurate QRS complex identification

### 3. Heart Rate Calculation
- Real-time BPM calculation from RR intervals
- Large, readable BPM display
- Running average for stable readings

### 4. Clinical Alert System
- **Bradycardia**: Alerts when heart rate < 60 BPM
- **Tachycardia**: Alerts when heart rate > 100 BPM
- **Sudden Changes**: Detects BPM changes > 20 within 10 seconds
- Visual pulse animation for active alerts

### 5. Email & SMS Notification System
- **Email Alerts**: Automatic email notifications via Gmail integration
- **SMS Alerts**: Text message notifications (requires Twilio setup)
- **Clinical Recommendations**: Detailed medical guidance for each alert
- **Immediate Action Steps**: Critical next steps for healthcare providers
- **Cooldown System**: Prevents alert fatigue (5-minute cooldown per alert type)
- **Configurable Settings**: Easy setup through settings modal

### 6. Clinical Suggestions & Recommendations
- **Evidence-Based Guidance**: Medical recommendations for each condition
- **Severity Classification**: High/Medium priority alerts
- **Action Plans**: Immediate actions and long-term recommendations
- **Patient Assessment Tips**: What to check, monitor, and document
- **Interactive Display**: Real-time clinical suggestions panel

### 7. Modern Medical UI
- Clean, professional interface
- Scrolling waveform display (1500 sample window)
- Gradient backgrounds for metrics
- Notification settings modal
- Clinical suggestions panel
- Responsive design for all screen sizes

## Technical Implementation

### WebSocket Data Format
Each chunk sent from backend to frontend contains:
```json
{
  "t0": 0.0,                    // Start time in seconds
  "fs": 360,                    // Sampling frequency
  "samples": [...],             // ECG amplitude values
  "peaks": [12, 156],           // R-peak indices within chunk
  "bpm": 72.5,                  // Current heart rate
  "alerts": ["..."],            // Active clinical alerts
  "clinical_suggestions": [{    // Clinical recommendations
    "title": "Alert Title",
    "description": "...",
    "severity": "HIGH|MEDIUM",
    "immediate_actions": [...],
    "recommendations": [...]
  }]
}
```

### Signal Processing Pipeline
1. Load MIT-BIH record using wfdb.rdrecord()
2. Detect all R-peaks using gqrs_detect()
3. Stream signal in 128-sample chunks
4. Calculate BPM from RR intervals
5. Check for clinical alert conditions
6. Emit data via WebSocket to frontend

### Frontend Visualization
1. Receive ECG chunks via Socket.IO
2. Update Chart.js with new samples
3. Add R-peak markers as scatter points
4. Maintain 1500-sample rolling window
5. Update BPM display and alerts panel

## How to Use

1. **Configure Notifications** (First Time Setup):
   - Click "⚙️ Notification Settings" button
   - Enable Email Alerts and enter your email address
   - (Optional) Enable SMS Alerts and enter phone number (requires Twilio setup)
   - Click "Save Settings"

2. **Start Monitoring**: Click "Start Monitoring" button

3. **View Real-Time ECG**: Watch the live ECG waveform with R-peak markers

4. **Monitor Heart Rate**: Check the large BPM display for current heart rate

5. **Check Alerts**: Review any clinical alerts in the alerts panel

6. **Review Clinical Suggestions**: If an alert occurs, detailed clinical recommendations appear below the controls

7. **Receive Notifications**: 
   - Email alerts sent automatically with full clinical guidance
   - SMS alerts for critical conditions (if configured)
   - Cooldown period prevents duplicate alerts

8. **Stop Monitoring**: Click "Stop Monitoring" to pause

## Data Source
- **Database**: MIT-BIH Arrhythmia Database
- **Record**: 100 (representative normal sinus rhythm)
- **Source**: PhysioNet (https://physionet.org)
- **Sampling Rate**: 360 Hz
- **Lead**: Modified Lead II

## Recent Changes

- **2024-11-22 (Update 2)**: Email/SMS Notification System
  - Added notification_handler.py with Gmail integration
  - Email alerts with clinical recommendations and HTML formatting
  - SMS notification support (requires Twilio connector setup)
  - Configurable notification settings via modal UI
  - Clinical suggestions panel with immediate actions and recommendations
  - Alert cooldown system to prevent notification fatigue
  - Real-time notification status display
  - Severity-based alert classification (HIGH/MEDIUM)

- **2024-11-22 (Initial)**: Initial project creation
  - Complete backend implementation with Flask-SocketIO
  - R-peak detection using GQRS algorithm
  - Real-time streaming with 128-sample chunks
  - Clinical alert system for arrhythmia detection
  - Modern responsive web interface
  - Chart.js integration for live visualization

## Performance Considerations
- Eventlet async mode for efficient concurrent connections
- Chart.js animation disabled for smooth performance
- Rolling window prevents memory growth
- Background threading for non-blocking streaming

## Integrations

### Gmail (Active)
- Used for sending email alerts with clinical recommendations
- Automatically managed via Replit Gmail connector
- No API key management required

### Twilio (Optional)
- For SMS alert notifications
- Requires user to authorize the Twilio connector
- Note: User declined setup during initial configuration
- Can be enabled later by authorizing Twilio connector in Replit

## Future Enhancements
- Multiple ECG lead support (II, V1, V5)
- Playback controls (pause, resume, speed adjustment)
- ECG recording export (CSV, PDF reports)
- Historical data view with timeline scrubbing
- Advanced arrhythmia detection (PVCs, AF, heart blocks)
- Patient profile management
- Custom alert thresholds configuration
- Alert history and analytics dashboard
