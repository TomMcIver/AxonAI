from flask import jsonify, request, session
from app import app, db
from models import User, Class, ChatMessage, TokenUsage
from auth import login_required
from datetime import datetime
import json

# Initialize AI service
try:
    from ai_service import AIService
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

        # For mock users (negative IDs), return a demo response
        if not user_id or user_id < 0:
            return jsonify({
                'success': True,
                'message': message,
                'response': _demo_response(message),
                'timestamp': datetime.now().isoformat()
            })

        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': True,
                'message': message,
                'response': _demo_response(message),
                'timestamp': datetime.now().isoformat()
            })

        # Check enrollment
        class_obj = Class.query.get(class_id)
        if not class_obj or user not in class_obj.users:
            return jsonify({
                'success': True,
                'message': message,
                'response': _demo_response(message),
                'timestamp': datetime.now().isoformat()
            })

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

        # Fallback demo response
        return jsonify({
            'success': True,
            'message': message,
            'response': _demo_response(message),
            'timestamp': datetime.now().isoformat()
        })

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


def _demo_response(message):
    """Generate a simple demo response when AI service is unavailable"""
    msg_lower = message.lower()

    if any(w in msg_lower for w in ['explain', 'what is', 'what are', 'how does']):
        return (
            "Great question! Let me break this down for you. "
            "This concept involves understanding the fundamental principles and how they connect to what we've been learning. "
            "Would you like me to go through a specific example, or would you prefer a step-by-step walkthrough?"
        )
    elif any(w in msg_lower for w in ['practice', 'problem', 'exercise', 'quiz']):
        return (
            "Here's a practice problem for you:\n\n"
            "Try solving this step by step, and let me know if you need hints along the way. "
            "Remember to show your work so I can help identify any areas where you might need extra practice."
        )
    elif any(w in msg_lower for w in ['mistake', 'wrong', 'error', 'help']):
        return (
            "No worries - mistakes are how we learn! "
            "Let's look at this together. Can you walk me through your thinking? "
            "That way I can pinpoint exactly where things went off track and we can work through it step by step."
        )
    else:
        return (
            "I understand your question. Let me think about the best way to help you with this. "
            "Could you provide a bit more context so I can give you the most helpful explanation? "
            "For example, are you working on a specific assignment, or is this a general concept question?"
        )
