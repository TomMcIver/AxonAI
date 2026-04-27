from flask import jsonify, request, session
from app import app, db
from models.models import User, Class, ChatMessage, TokenUsage
from utils.auth import login_required
from datetime import datetime
import json

# Initialize AI service
try:
    from core.ai_service import AIService
    ai_service = AIService()
except Exception:
    ai_service = None


@app.route('/api/chat/send', methods=['POST'])
@login_required
def send_chat_message():
    """Send a message to the AI chatbot (student only, DB integrated)"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        class_id = data.get('class_id')

        if not message or not class_id:
            return jsonify({'error': 'Message and class_id are required'}), 400

        user_id = session.get('user_id')

        # For mock users (negative IDs), return a neutral transport error
        if not user_id or user_id < 0:
            return jsonify({'error': 'tutor unavailable', 'detail': 'please try again'}), 503

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'tutor unavailable', 'detail': 'please try again'}), 503

        # Check enrollment
        class_obj = Class.query.get(class_id)
        if not class_obj or user not in class_obj.users:
            return jsonify({'error': 'tutor unavailable', 'detail': 'please try again'}), 503

        # Try AI service
        if ai_service:
            try:
                response = ai_service.generate_response(message, user_id, class_id)
                if response:
                    return jsonify({
                        'success': True,
                        'message': message,
                        'response': response,
                        'timestamp': datetime.now().isoformat()
                    })
            except Exception:
                pass

        return jsonify({'error': 'tutor unavailable', 'detail': 'please try again'}), 503

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat/history/<int:class_id>')
@login_required
def get_chat_history(class_id):
    """Get chat history for a class"""
    user_id = session.get('user_id')
    if not user_id or user_id < 0:
        return jsonify({'messages': []})

    try:
        messages = ChatMessage.query.filter_by(
            user_id=user_id, class_id=class_id
        ).order_by(ChatMessage.created_at.asc()).all()

        result = []
        for msg in messages:
            result.append({
                'message': msg.message,
                'response': msg.response,
                'created_at': msg.created_at.isoformat() if msg.created_at else None
            })
        return jsonify({'messages': result})
    except Exception:
        return jsonify({'messages': []})


