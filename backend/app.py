# backend/app.py

import os
import numpy as np
import faiss
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
import uuid
import json
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

# 1. Инициализация и конфигурация
# ----------------------------------------------------
load_dotenv()

app = Flask(__name__)
# CORS необходим, чтобы ваш фронтенд на Vue мог общаться с бэкендом
CORS(app)

# Конфигурация базы данных SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация SQLAlchemy и Migrate
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Инициализация клиента OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Параметры RAG (пока остаются, но будут интегрированы с БД позже)
EMBEDDING_DIMENSION = 1536
LONG_TERM_MEMORY_TOP_K = 2

# 2. Модели базы данных (Структура наших данных)
# ----------------------------------------------------

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default="Новый проект")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    chats = db.relationship('Chat', backref='project', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "chat_count": len(self.chats)
        }

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default="Новый чат")
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='chat', lazy='dynamic', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "project_id": self.project_id,
            "created_at": self.created_at.isoformat()
        }

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat()
        }

# 3. API для управления Проектами
# ----------------------------------------------------

@app.route('/api/projects', methods=['POST'])
def create_project():
    data = request.json or {}
    new_project = Project(name=data.get('name', 'Новый проект'))
    db.session.add(new_project)
    db.session.commit()
    return jsonify(new_project.to_dict()), 201

@app.route('/api/projects', methods=['GET'])
def get_projects():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return jsonify([p.to_dict() for p in projects])

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def rename_project(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.json
    if 'name' in data:
        project.name = data['name']
        db.session.commit()
    return jsonify(project.to_dict())

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Project deleted successfully'})

# 4. API для управления Чатами
# ----------------------------------------------------

@app.route('/api/projects/<int:project_id>/chats', methods=['POST'])
def create_chat(project_id):
    Project.query.get_or_404(project_id) # Проверяем, что проект существует
    data = request.json or {}
    new_chat = Chat(name=data.get('name', 'Новый чат'), project_id=project_id)
    db.session.add(new_chat)
    db.session.commit()
    return jsonify(new_chat.to_dict()), 201

@app.route('/api/projects/<int:project_id>/chats', methods=['GET'])
def get_chats_for_project(project_id):
    project = Project.query.get_or_404(project_id)
    chats = Chat.query.filter_by(project_id=project.id).order_by(Chat.created_at.desc()).all()
    return jsonify([c.to_dict() for c in chats])

@app.route('/api/chats/<int:chat_id>', methods=['PUT'])
def rename_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    data = request.json
    if 'name' in data:
        chat.name = data['name']
        db.session.commit()
    return jsonify(chat.to_dict())

@app.route('/api/chats/<int:chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    db.session.delete(chat)
    db.session.commit()
    return jsonify({'message': 'Chat deleted successfully'})

# 5. API для Сообщений (пока без RAG и streaming)
# ----------------------------------------------------

@app.route('/api/chats/<int:chat_id>/messages', methods=['GET'])
def get_messages(chat_id):
    page = request.args.get('page', 1, type=int)
    per_page = 20 # Количество сообщений на одной "странице"

    chat = Chat.query.get_or_404(chat_id)
    messages_pagination = chat.messages.order_by(Message.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'messages': [m.to_dict() for m in messages_pagination.items],
        'has_next': messages_pagination.has_next,
        'current_page': messages_pagination.page
    })

# /api/chat - старый эндпоинт, переименован для ясности
@app.route('/api/chats/<int:chat_id>/messages', methods=['POST'])
def send_message(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    user_message_content = request.json.get('message')

    if not user_message_content:
        return jsonify({"error": "Message is required"}), 400

    # Сохраняем сообщение пользователя в БД
    user_message = Message(chat_id=chat.id, role='user', content=user_message_content)
    db.session.add(user_message)
    db.session.commit()

    # --- Сборка контекста для модели ---
    # Временное упрощение: берем последние 10 сообщений
    history = chat.messages.order_by(Message.created_at.desc()).limit(10).all()
    history.reverse() # Восстанавливаем хронологический порядок

    messages_for_prompt = [{"role": m.role, "content": m.content} for m in history]

    # Пока не добавляем системный промпт, это следующий этап
    # messages_for_prompt.insert(0, {"role": "system", "content": "..."})

    # --- Вызов OpenAI ---
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", # В вашем коде был gpt-5, я заменил на доступную модель
        messages=messages_for_prompt
    )
    bot_message_content = response.choices[0].message.content

    # Сохраняем ответ ассистента в БД
    bot_message = Message(chat_id=chat.id, role='assistant', content=bot_message_content)
    db.session.add(bot_message)
    db.session.commit()

    return jsonify(bot_message.to_dict())


if __name__ == '__main__':
    # Создаем все таблицы при первом запуске (если их нет)
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)

# 1.  **Установите зависимости:** `pip install -r backend/requirements.txt`
# 2.  **Инициализируйте базу данных:**
#     Находясь в папке `backend`, выполните в терминале:
#     ```bash
#     flask db init
#     flask db migrate -m "Initial migration."
#     flask db upgrade

