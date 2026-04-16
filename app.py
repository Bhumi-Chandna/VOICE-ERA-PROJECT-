#!/usr/bin/env python3
"""
SignMeet Flask Application
A video calling platform with ISL recognition converted from React to Flask
"""

import os
import uuid
import base64
import numpy as np
import cv2
import mediapipe as mp
import tensorflow as tf
import joblib
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from dotenv import load_dotenv
from markupsafe import Markup
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Backwards-compatible Jinja filter: tojsonhtml
# Some templates (or older examples) use `tojsonhtml`. Register it to avoid TemplateAssertionError.
def _tojsonhtml(value):
    # json.dumps will produce valid JS literal (strings quoted). Markup() ensures Jinja doesn't escape it.
    return Markup(json.dumps(value))
app.jinja_env.filters['tojsonhtml'] = _tojsonhtml

# Initialize Flask-SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=True,
    engineio_logger=False
)

# Initialize MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Global variables for ML model
model = None
labels = None

# In-memory storage for rooms and participants (replaces MongoDB)
rooms = {}
participants = {}
captions_history = {}

def load_ml_model():
    """Load TensorFlow model and labels on startup"""
    global model, labels
    try:
        model_path = Path('models/sign_model.h5')
        labels_path = Path('models/labels.joblib')
        
        if model_path.exists() and labels_path.exists():
            model = tf.keras.models.load_model(str(model_path))
            labels = joblib.load(str(labels_path))
            logger.info(f"Model loaded successfully. Classes: {len(labels)}")
            return True
        else:
            logger.warning("Model files not found. Sign recognition will be disabled.")
            return False
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return False

def extract_landmarks(image):
    """Extract MediaPipe landmarks from image"""
    try:
        # Convert image to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        landmarks_array = np.zeros(63)  # 21*3 = 63 for hand landmarks
        
        # Process hands
        with mp_hands.Hands(
            static_image_mode=True,
            max_num_hands=1,
            min_detection_confidence=0.5
        ) as hands:
            results = hands.process(rgb_image)
            
            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                for i, landmark in enumerate(hand_landmarks.landmark):
                    if i < 21:  # Only use first 21 landmarks
                        landmarks_array[i*3] = landmark.x
                        landmarks_array[i*3+1] = landmark.y
                        landmarks_array[i*3+2] = landmark.z
        
        return landmarks_array
    except Exception as e:
        logger.error(f"Error extracting landmarks: {e}")
        return np.zeros(63)

def predict_sign(image_data: str):
    """Predict sign language from base64 image"""
    try:
        if model is None or labels is None:
            return None, 0.0
        
        # Decode base64 image
        if ',' in image_data:
            image_bytes = base64.b64decode(image_data.split(',')[1])
        else:
            image_bytes = base64.b64decode(image_data)
        
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return None, 0.0
        
        # Resize image to model input size (128x128)
        image_resized = cv2.resize(image, (128, 128))
        image_normalized = image_resized.astype(np.float32) / 255.0
        image_batch = np.expand_dims(image_normalized, axis=0)
        
        # Extract landmarks
        landmarks = extract_landmarks(image)
        landmarks_batch = np.expand_dims(landmarks, axis=0)
        
        # Make prediction
        prediction = model.predict([image_batch, landmarks_batch], verbose=0)
        predicted_class = np.argmax(prediction[0])
        confidence = float(np.max(prediction[0]))
        
        predicted_label = labels[predicted_class]
        
        return predicted_label, confidence
    except Exception as e:
        logger.error(f"Error in prediction: {e}")
        return None, 0.0

# Utility: broadcast current participants list+count to a room
def broadcast_participants(room_id):
    try:
        if room_id not in rooms:
            return
        lst = []
        for pid in rooms[room_id]['participants']:
            p = participants.get(pid)
            if p:
                lst.append({
                    'participant_id': pid,
                    'participant_name': p.get('name', 'Unknown'),
                    'sid': p.get('sid')
                })
        payload = {'participants': lst, 'count': len(lst)}
        socketio.emit('participant_list', payload, room=room_id)
        logger.debug(f"Broadcasted participants for room {room_id}: {payload}")
    except Exception as e:
        logger.error(f"Error broadcasting participants for room {room_id}: {e}")

# Flask Routes
@app.route('/')
def index():
    """Home page for creating/joining rooms"""
    return render_template('index.html')

@app.route('/room/<room_id>')
def room(room_id):
    """Room page for video calling"""
    # Generate a participant ID for this session
    participant_id = str(uuid.uuid4())

    # Provide default ICE servers so the client can create RTCPeerConnection easily.
    # Client should use window.ROOM_DATA.iceServers when creating peer connections.
    default_ice_servers = [
        {"urls": "stun:stun.l.google.com:19302"},
        # If you have a TURN server, add it here for production / mobile reliability:
        # {"urls": "turn:turn.example.com:3478", "username": "user", "credential": "pass"}
    ]

    return render_template(
        'room.html',
        room_id=room_id,
        participant_id=participant_id,
        ice_servers=default_ice_servers
    )

@app.route('/api/predict', methods=['POST'])
def predict_sign_language():
    """API endpoint for sign language prediction"""
    try:
        data = request.get_json()
        image_data = data.get('image_data')
        room_id = data.get('room_id')
        participant_id = data.get('participant_id')
        
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        predicted_text, confidence = predict_sign(image_data)
        
        if predicted_text and confidence > 0.7:  # Confidence threshold
            # Get participant info
            participant = participants.get(participant_id, {'name': 'Unknown'})
            
            # Create caption
            caption = {
                'id': str(uuid.uuid4()),
                'text': predicted_text,
                'participant_name': participant['name'],
                'room_id': room_id,
                'confidence': confidence,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Store caption
            if room_id not in captions_history:
                captions_history[room_id] = []
            captions_history[room_id].append(caption)
            
            # Keep only last 50 captions per room
            if len(captions_history[room_id]) > 50:
                captions_history[room_id] = captions_history[room_id][-50:]
            
            # Broadcast caption to room
            socketio.emit('new_caption', caption, room=room_id)
            
            return jsonify({
                'predicted_text': predicted_text,
                'confidence': confidence,
                'caption': caption
            })
        
        return jsonify({
            'predicted_text': None,
            'confidence': confidence if confidence else 0.0
        })
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({'error': 'Prediction failed'}), 500

@app.route('/api/rooms/<room_id>/captions')
def get_room_captions(room_id):
    """Get recent captions for a room"""
    captions = captions_history.get(room_id, [])
    return jsonify(captions[-20:])  # Return last 20 captions

# Socket.IO Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client {request.sid} connected")
    emit('connected', {'sid': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client {request.sid} disconnected")
    
    # Clean up participant data
    participant_id = None
    for pid, pdata in list(participants.items()):
        if pdata.get('sid') == request.sid:
            participant_id = pid
            break
    
    if participant_id:
        participant = participants.pop(participant_id, None)
        if participant:
            room_id = participant.get('room_id')
            if room_id and room_id in rooms:
                rooms[room_id]['participants'] = [
                    p for p in rooms[room_id]['participants'] if p != participant_id
                ]
                # Notify room that user left
                emit('user_left', {
                    'participant_id': participant_id,
                    'participant_name': participant.get('name', 'Unknown')
                }, room=room_id)
                # Broadcast updated participants
                broadcast_participants(room_id)

@socketio.on('join_room')
def handle_join_room(data):
    """Handle joining a Socket.IO room"""
    try:
        room_id = data.get('room_id')
        participant_name = data.get('participant_name', 'Anonymous')
        participant_id = data.get('participant_id')
        
        if not room_id or not participant_id:
            emit('error', {'message': 'Missing room_id or participant_id'})
            return
        
        # Create room if it doesn't exist
        if room_id not in rooms:
            rooms[room_id] = {
                'id': room_id,
                'participants': [],
                'created_at': datetime.utcnow().isoformat()
            }
        
        # If participant already exists with different SID, update it
        existing = participants.get(participant_id)
        if existing and existing.get('sid') != request.sid:
            logger.info(f"Updating SID for participant {participant_id} from {existing.get('sid')} to {request.sid}")
            existing['sid'] = request.sid
            existing['room_id'] = room_id
            existing['joined_at'] = datetime.utcnow().isoformat()
            existing['name'] = participant_name
        else:
            # Create/update participant
            participants[participant_id] = {
                'id': participant_id,
                'name': participant_name,
                'room_id': room_id,
                'sid': request.sid,
                'joined_at': datetime.utcnow().isoformat()
            }
        
        # Add participant to room
        if participant_id not in rooms[room_id]['participants']:
            rooms[room_id]['participants'].append(participant_id)
        
        # Join Socket.IO room
        join_room(room_id)
        
        # Notify others in the room (existing users)
        emit('user_joined', {
            'participant_id': participant_id,
            'participant_name': participant_name,
            'sid': request.sid
        }, room=room_id, include_self=False)
        
        # Send current participants list to the new user
        current_participants = []
        for pid in rooms[room_id]['participants']:
            if pid in participants:
                p = participants[pid]
                current_participants.append({
                    'participant_id': pid,
                    'participant_name': p['name'],
                    'sid': p['sid']
                })
        
        emit('current_participants', current_participants)
        
        logger.info(f"Participant {participant_name} ({participant_id}) joined room {room_id}")
        
        # Broadcast authoritative participants list and count to everyone in the room
        broadcast_participants(room_id)
        
    except Exception as e:
        logger.error(f"Error in join_room: {e}")
        emit('error', {'message': 'Failed to join room'})

@socketio.on('leave_room')
def handle_leave_room(data):
    """Handle leaving a Socket.IO room"""
    try:
        room_id = data.get('room_id')
        participant_id = data.get('participant_id')
        
        if room_id and participant_id and participant_id in participants:
            participant = participants[participant_id]
            participant_name = participant.get('name', 'Unknown')
            
            # Remove from room
            if room_id in rooms:
                rooms[room_id]['participants'] = [
                    p for p in rooms[room_id]['participants'] if p != participant_id
                ]
            
            # Leave Socket.IO room
            leave_room(room_id)
            
            # Notify others
            emit('user_left', {
                'participant_id': participant_id,
                'participant_name': participant_name
            }, room=room_id)
            
            # Clean up participant data
            participants.pop(participant_id, None)
            
            # Broadcast updated participants
            broadcast_participants(room_id)
            
            logger.info(f"Participant {participant_name} left room {room_id}")
            
    except Exception as e:
        logger.error(f"Error in leave_room: {e}")

# WebRTC Signaling Events
@socketio.on('webrtc_offer')
def handle_webrtc_offer(data):
    """Handle WebRTC offer"""
    try:
        target_sid = data.get('target_sid')
        offer = data.get('offer')
        participant_id = data.get('participant_id')
        
        emit('webrtc_offer', {
            'offer': offer,
            'from_sid': request.sid,
            'from_participant_id': participant_id
        }, room=target_sid)
        
    except Exception as e:
        logger.error(f"Error in webrtc_offer: {e}")

@socketio.on('webrtc_answer')
def handle_webrtc_answer(data):
    """Handle WebRTC answer"""
    try:
        target_sid = data.get('target_sid')
        answer = data.get('answer')
        participant_id = data.get('participant_id')
        
        emit('webrtc_answer', {
            'answer': answer,
            'from_sid': request.sid,
            'from_participant_id': participant_id
        }, room=target_sid)
        
    except Exception as e:
        logger.error(f"Error in webrtc_answer: {e}")

@socketio.on('webrtc_ice_candidate')
def handle_webrtc_ice_candidate(data):
    """Handle WebRTC ICE candidate"""
    try:
        target_sid = data.get('target_sid')
        candidate = data.get('candidate')
        participant_id = data.get('participant_id')
        
        emit('webrtc_ice_candidate', {
            'candidate': candidate,
            'from_sid': request.sid,
            'from_participant_id': participant_id
        }, room=target_sid)
        
    except Exception as e:
        logger.error(f"Error in webrtc_ice_candidate: {e}")

# Chat Events
@socketio.on('send_message')
def handle_send_message(data):
    """Handle chat messages"""
    try:
        room_id = data.get('room_id')
        message = data.get('message', '').strip()
        participant_id = data.get('participant_id')
        
        if not message or not room_id or not participant_id:
            return
        
        participant = participants.get(participant_id, {'name': 'Unknown'})
        
        message_data = {
            'id': str(uuid.uuid4()),
            'message': message,
            'participant_name': participant['name'],
            'participant_id': participant_id,
            'timestamp': datetime.utcnow().isoformat(),
            'room_id': room_id
        }
        
        emit('new_message', message_data, room=room_id)
        logger.info(f"Message from {participant['name']} in room {room_id}: {message}")
        
    except Exception as e:
        logger.error(f"Error in send_message: {e}")

# Sign Recognition Events
@socketio.on('predict_frame')
def handle_predict_frame(data):
    """Handle real-time frame prediction"""
    try:
        image_data = data.get('image_data')
        room_id = data.get('room_id')
        participant_id = data.get('participant_id')
        
        if not image_data or not participant_id:
            return
        
        predicted_text, confidence = predict_sign(image_data)
        
        if predicted_text and confidence > 0.7:
            participant = participants.get(participant_id, {'name': 'Unknown'})
            
            caption = {
                'id': str(uuid.uuid4()),
                'text': predicted_text,
                'participant_name': participant['name'],
                'participant_id': participant_id,
                'room_id': room_id,
                'confidence': confidence,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Store caption
            if room_id not in captions_history:
                captions_history[room_id] = []
            captions_history[room_id].append(caption)
            
            # Keep only last 50 captions
            if len(captions_history[room_id]) > 50:
                captions_history[room_id] = captions_history[room_id][-50:]
            
            # Broadcast to room
            emit('new_caption', caption, room=room_id)
        
        # Send result back to sender for immediate feedback
        emit('prediction_result', {
            'predicted_text': predicted_text,
            'confidence': confidence
        })
        
    except Exception as e:
        logger.error(f"Error in predict_frame: {e}")

if __name__ == '__main__':
    # Load ML model on startup
    load_ml_model()
    
    # Create models directory if it doesn't exist
    os.makedirs('models', exist_ok=True)
    
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=os.environ.get('FLASK_ENV') == 'development'
    )
