<<<<<<< HEAD
# SignMeet Flask - Complete Setup and Usage Guide

## Overview

SignMeet Flask is a complete conversion of the React-based SignMeet application to a pure Flask backend with Jinja2 templates and vanilla JavaScript. This application provides real-time video calling with integrated Indian Sign Language (ISL) recognition, maintaining all the original functionality while eliminating dependencies on React, Node.js, and MongoDB.

## 🌟 Features

### Core Video Calling
- **Multi-participant video calls** (up to 6 participants)
- **WebRTC peer-to-peer connections** for high-quality video/audio
- **Room-based system** with unique room IDs
- **Camera and microphone controls** (mute/unmute, video on/off)
- **Screen sharing support**
- **Graceful fallback** for users without camera/microphone access

### Sign Language Recognition
- **Real-time ISL recognition** using TensorFlow model
- **106 sign classes** including ISL Alphabet, numbers, and common words
- **MediaPipe integration** for hand landmark detection
- **Live captions** with confidence scores
- **Real-time frame processing** via WebSocket events

### Communication Features
- **Real-time chat** during video calls
- **Live caption display** with participant names
- **Shared caption area** for all participants
- **Message and caption history**

### User Experience
- **Modern glassmorphism UI** with Tailwind CSS
- **Fully responsive design** for desktop and mobile
- **Professional controls** similar to Google Meet/Zoom
- **Real-time updates** via Flask-SocketIO
- **Error handling** and graceful degradation

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ (tested with Python 3.9-3.11)
- Modern web browser with WebRTC support (Chrome, Firefox, Edge, Safari)
- Webcam and microphone (optional but recommended)

### Installation

1. **Create and activate virtual environment**
```bash
python -m venv signmeet_env
# On Windows:
signmeet_env\Scripts\activate
# On macOS/Linux:
source signmeet_env/bin/activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Environment setup**
```bash
cp .env.example .env
# Edit .env with your preferred settings
```

4. **Create required directories**
```bash
mkdir -p models static/images
```

5. **Add ML models (optional)**
Place your trained ISL model files in the `models/` directory:
- `sign_model.h5` - TensorFlow/Keras model
- `labels.joblib` - Class labels file

If you don't have these files, the app will run without sign recognition features.

### Running the Application

1. **Development mode**
```bash
python app.py
```

2. **Production mode with Gunicorn**
```bash
pip install gunicorn
gunicorn --worker-class eventlet -w 1 app:app --bind 0.0.0.0:5000
```

3. **Access the application**
- Open http://localhost:5000 in your browser
- Enter your name and create/join a room
- Allow camera/microphone permissions when prompted

## 🌐 Remote Testing with ngrok

For testing with friends or across different networks:

1. **Install ngrok**
```bash
# Download from https://ngrok.com/download
# Or install via package manager
npm install -g ngrok
```

2. **Expose your Flask server**
```bash
# In a new terminal, while your Flask app is running
ngrok http 5000
```

3. **Share the ngrok URL**
- Copy the HTTPS URL from ngrok (e.g., `https://abc123.ngrok.io`)
- Share this URL with others to join your rooms
- Everyone can access the app through this URL

## 📁 Project Structure

```
signmeet_flask/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
├── README.md            # This file
├── templates/           # Jinja2 HTML templates
│   ├── base.html        # Base template with common elements
│   ├── index.html       # Home/join page
│   └── room.html        # Video call room page
├── static/              # Static assets
│   ├── css/
│   │   └── styles.css   # Custom CSS styles
│   ├── js/
│   │   └── app.js       # Vanilla JavaScript client code
│   └── images/          # Images and icons
└── models/              # ML models (optional)
    ├── sign_model.h5    # TensorFlow ISL model
    └── labels.joblib    # Class labels
```

## 🔧 Configuration Options

### Environment Variables (.env)

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development  # or production
FLASK_DEBUG=True

# Server Configuration
HOST=0.0.0.0
PORT=5000

# ML Model Settings
MODEL_PATH=models/sign_model.h5
LABELS_PATH=models/labels.joblib
CONFIDENCE_THRESHOLD=0.7
MAX_PARTICIPANTS_PER_ROOM=6

# Logging
LOG_LEVEL=INFO
```

### Production Deployment

For production deployment, update your `.env`:

```bash
SECRET_KEY=your-production-secret-key
FLASK_ENV=production
FLASK_DEBUG=False
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

## 🤖 Machine Learning Integration

### Model Requirements
The application expects:
- **TensorFlow/Keras model** (.h5 file) trained for ISL recognition
- **Labels file** (.joblib) containing class names
- **Input format**: 
  - Image: 128x128x3 RGB
  - Landmarks: 63 features (21 hand landmarks × 3 coordinates)

### Model Loading
- Models are loaded once at startup for optimal performance
- If model files are missing, the app runs without sign recognition
- Real-time prediction via WebSocket events (1 FPS)

### Supported Signs (Example)
The original model recognizes:
- **Alphabet**: A-Z (ISL alphabet signs)
- **Numbers**: 1, 3-9
- **Common words**: accept, age, bag, book, help, home, idea, namastey, school, technology, etc.

## 🎯 API Endpoints

### Flask Routes
- `GET /` - Home page (join/create room)
- `GET /room/<room_id>` - Video call room page
- `POST /api/predict` - Sign language prediction (REST)
- `GET /api/rooms/<room_id>/captions` - Get room captions

### WebSocket Events (Flask-SocketIO)
- `join_room` - Join a room
- `leave_room` - Leave a room
- `webrtc_offer/answer/ice_candidate` - WebRTC signaling
- `send_message` - Send chat messages
- `predict_frame` - Real-time sign recognition
- `new_caption` - Broadcast new captions
- `new_message` - Broadcast chat messages

## 🛠️ Development

### Code Structure
- **Flask Routes**: Minimal REST endpoints for page rendering
- **Socket.IO Handlers**: Real-time communication and WebRTC signaling
- **WebRTC**: Peer-to-peer video/audio in vanilla JavaScript
- **ML Pipeline**: TensorFlow + MediaPipe for sign recognition
- **UI Components**: Jinja2 templates + Tailwind CSS + vanilla JS

### Adding New Features
1. **Backend**: Add Socket.IO events in `app.py`
2. **Frontend**: Extend the `SignMeetApp` class in `app.js`
3. **UI**: Update Jinja2 templates and Tailwind CSS classes
4. **Styles**: Add custom CSS in `static/css/styles.css`

### Testing
- **Local testing**: Multiple browser windows/tabs
- **Remote testing**: Use ngrok for cross-network testing
- **Mobile testing**: Responsive design works on mobile browsers
- **WebRTC testing**: Test audio/video with different network conditions

## 🔍 Troubleshooting

### Common Issues

1. **Camera/Microphone Access Denied**
   - Solution: Grant permissions in browser settings
   - Fallback: App works in chat-only mode without media

2. **WebRTC Connection Failed**
   - Solution: Check firewall settings and network configuration
   - Note: NAT traversal handled by STUN servers

3. **Sign Recognition Not Working**
   - Check: Model files in `models/` directory
   - Check: Camera access granted and good lighting
   - Check: Browser console for error messages

4. **Socket.IO Connection Issues**
   - Check: Flask server is running and accessible
   - Check: No proxy/firewall blocking WebSocket connections
   - Try: Refresh the page or restart the server

5. **Performance Issues**
   - Reduce: Video quality in WebRTC settings
   - Disable: Sign recognition if not needed
   - Check: System resources and network bandwidth

### Browser Compatibility
- ✅ **Chrome 80+**: Full support
- ✅ **Firefox 75+**: Full support  
- ✅ **Edge 80+**: Full support
- ✅ **Safari 14+**: Full support
- ❌ **IE**: Not supported (no WebRTC)

### Network Requirements
- **Bandwidth**: 1 Mbps minimum, 5+ Mbps recommended per participant
- **Latency**: <200ms for optimal experience
- **Firewall**: Allow WebRTC ports (varies by network)

## 📊 Performance Optimization

### Client-Side
- WebRTC peer-to-peer reduces server load
- Efficient DOM manipulation with vanilla JS
- CSS animations with hardware acceleration
- Image compression for sign recognition

### Server-Side
- Single model loading at startup
- In-memory storage for session data
- Efficient Socket.IO event handling
- Configurable frame rate for sign recognition

## 🔒 Security Considerations

### Development
- HTTPS recommended for WebRTC (required for some browsers)
- CORS configured for local development
- No persistent data storage (privacy by design)

### Production
- Use strong SECRET_KEY
- Enable secure cookie settings
- Deploy behind reverse proxy (nginx/Apache)
- Consider rate limiting for API endpoints

## 📱 Mobile Support

The application is fully responsive and supports:
- **Touch controls**: Tap to mute/unmute, toggle video
- **Portrait/landscape**: Adaptive layouts
- **Mobile browsers**: Chrome Mobile, Safari Mobile, Firefox Mobile
- **Camera switching**: Front/back camera support

## 🎨 UI/UX Features

### Design System
- **Tailwind CSS**: Utility-first styling
- **Glassmorphism**: Modern frosted glass effects
- **Fredoka Font**: Friendly, accessible typography
- **Gradient Themes**: Primary colors from purple to blue

### Interactions
- **Smooth animations**: CSS transitions and transforms
- **Hover effects**: Interactive feedback
- **Loading states**: Visual feedback during operations
- **Error handling**: User-friendly error messages

## 🤝 Contributing

This is a complete conversion from React to Flask. To contribute:

1. Follow the existing code structure
2. Maintain feature parity with original React version
3. Test on multiple browsers and devices
4. Ensure responsive design works correctly
5. Document any new features or changes

## 📄 License

This project maintains the same license as the original SignMeet application.

## 🆘 Support

For issues or questions:
1. Check this README for common solutions
2. Test with ngrok for remote connectivity issues  
3. Verify browser WebRTC compatibility
4. Check browser console for JavaScript errors
5. Ensure all dependencies are installed correctly

---

**SignMeet Flask** - Bridging communication gaps with technology, now powered by Flask! 🤟
=======
# VOICE-ERA-PROJECT-
A real-time video calling platform with integrated sign language recognition, designed to help deaf/mute individuals communicate effectively.
>>>>>>> e6f548c8985347e3a5434010d0e8ab7a9dbc6d6c
