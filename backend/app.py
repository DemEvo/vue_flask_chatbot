import os
import numpy as np
import faiss
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
import json
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from threading import Thread

# 1. Инициализация и конфигурация
# ----------------------------------------------------
load_dotenv()
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Параметры RAG
EMBEDDING_DIMENSION = 1536
LONG_TERM_MEMORY_TOP_K = 3
SHORT_TERM_MEMORY_MAX_MESSAGES = 6
VECTOR_STORE_PATH = "vector_stores"
os.makedirs(VECTOR_STORE_PATH, exist_ok=True)


# 2. Модели базы данных
# ----------------------------------------------------
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default="Новый проект")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    chats = db.relationship('Chat', backref='project', lazy=True, cascade="all, delete-orphan")
    prompts = db.relationship('Prompt', backref='project', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "created_at": self.created_at.isoformat(),
            'chats': [c.to_dict() for c in self.chats]
        }


class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default="Новый чат")
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='chat', lazy='dynamic', cascade="all, delete-orphan")
    active_prompt_id = db.Column(db.Integer, db.ForeignKey('prompt.id'), nullable=True)
    active_prompt = db.relationship('Prompt', lazy=True)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "project_id": self.project_id,
            "created_at": self.created_at.isoformat(),
            "active_prompt_id": self.active_prompt_id
        }


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Поле для связи с ID в векторной базе
    vector_id = db.Column(db.Integer, nullable=True, unique=True)

    def to_dict(self):
        return {"id": self.id, "role": self.role, "content": self.content, "created_at": self.created_at.isoformat()}


class Prompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "content": self.content, "project_id": self.project_id}


# 3. Менеджер Векторных Баз
# ----------------------------------------------------
class VectorStoreManager:
    def __init__(self, base_path):
        self.base_path = base_path
        self.stores = {}  # Кэш для загруженных индексов

    def _get_chat_path(self, chat_id):
        return os.path.join(self.base_path, f"chat_{chat_id}")

    def get_store(self, chat_id):
        if chat_id in self.stores:
            return self.stores[chat_id]

        chat_path = self._get_chat_path(chat_id)
        index_file = os.path.join(chat_path, "index.faiss")

        if os.path.exists(index_file):
            index = faiss.read_index(index_file)
        else:
            index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
            index = faiss.IndexIDMap(index)  # Обертка для использования ID сообщений

        self.stores[chat_id] = index
        return index

    def add_message(self, chat_id, message_obj):
        # Эта функция будет выполняться в фоновом потоке
        with app.app_context():
            store = self.get_store(chat_id)
            embedding = get_embedding(message_obj.content)

            # Используем ID сообщения из SQL как ID в Faiss
            store.add_with_ids(np.array([embedding], dtype=np.float32), np.array([message_obj.id]))

            # Обновляем запись в SQL, чтобы отметить, что она проиндексирована
            msg_to_update = Message.query.get(message_obj.id)
            if msg_to_update:
                msg_to_update.vector_id = message_obj.id
                db.session.commit()

            self.save_store(chat_id)

    def search(self, chat_id, query_text, k):
        store = self.get_store(chat_id)
        if store.ntotal == 0:
            return []

        query_embedding = get_embedding(query_text)
        distances, indices = store.search(np.array([query_embedding], dtype=np.float32), k)

        found_ids = [int(i) for i in indices[0] if i != -1]
        if not found_ids:
            return []

        return Message.query.filter(Message.id.in_(found_ids)).all()

    def save_store(self, chat_id):
        if chat_id in self.stores:
            chat_path = self._get_chat_path(chat_id)
            os.makedirs(chat_path, exist_ok=True)
            index_file = os.path.join(chat_path, "index.faiss")
            faiss.write_index(self.stores[chat_id], index_file)
            print(f"💾 Векторная база для чата {chat_id} сохранена.")


vector_manager = VectorStoreManager(VECTOR_STORE_PATH)


def get_embedding(text):
    response = client.embeddings.create(model="text-embedding-ada-002", input=text)
    return np.array(response.data[0].embedding)


# 4. API
# ----------------------------------------------------
# CRUD для проектов, чатов и промптов остаются БЕЗ ИЗМЕНЕНИЙ
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


@app.route('/api/projects/<int:project_id>/chats', methods=['POST'])
def create_chat(project_id):
    Project.query.get_or_404(project_id)
    data = request.json or {}
    new_chat = Chat(name=data.get('name', 'Новый чат'), project_id=project_id)
    db.session.add(new_chat)
    db.session.commit()
    return jsonify(new_chat.to_dict()), 201


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


@app.route('/api/projects/<int:project_id>/prompts', methods=['GET'])
def get_prompts(project_id):
    Project.query.get_or_404(project_id)
    prompts = Prompt.query.filter_by(project_id=project_id).all()
    return jsonify([p.to_dict() for p in prompts])


@app.route('/api/prompts', methods=['POST'])
def create_prompt():
    data = request.json
    new_prompt = Prompt(name=data['name'], content=data['content'], project_id=data['project_id'])
    db.session.add(new_prompt)
    db.session.commit()
    return jsonify(new_prompt.to_dict()), 201


@app.route('/api/prompts/<int:prompt_id>', methods=['PUT'])
def update_prompt(prompt_id):
    prompt = Prompt.query.get_or_404(prompt_id)
    data = request.json
    prompt.name = data.get('name', prompt.name)
    prompt.content = data.get('content', prompt.content)
    db.session.commit()
    return jsonify(prompt.to_dict())


@app.route('/api/prompts/<int:prompt_id>', methods=['DELETE'])
def delete_prompt(prompt_id):
    prompt = Prompt.query.get_or_404(prompt_id)
    db.session.delete(prompt)
    db.session.commit()
    return jsonify({'message': 'Prompt deleted'})


@app.route('/api/chats/<int:chat_id>/prompt', methods=['PUT'])
def set_chat_prompt(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    data = request.json
    prompt_id = data.get('prompt_id')
    chat.active_prompt_id = prompt_id
    db.session.commit()
    return jsonify(chat.to_dict())


@app.route('/api/chats/<int:chat_id>/messages', methods=['GET'])
def get_messages(chat_id):
    page = request.args.get('page', 1, type=int)
    per_page = 20
    chat = Chat.query.get_or_404(chat_id)
    messages_pagination = chat.messages.order_by(Message.created_at.desc()).paginate(page=page, per_page=per_page,
                                                                                     error_out=False)
    return jsonify({
        'messages': [m.to_dict() for m in messages_pagination.items],
        'has_next': messages_pagination.has_next,
        'current_page': messages_pagination.page,
        'active_prompt_id': chat.active_prompt_id
    })


# --- ОСНОВНОЙ ОБНОВЛЕННЫЙ ЭНДПОИНТ ---
@app.route('/api/chats/<int:chat_id>/messages', methods=['POST'])
def send_message(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    user_message_content = request.json.get('message')
    if not user_message_content: return jsonify({"error": "Message is required"}), 400

    user_message = Message(chat_id=chat.id, role='user', content=user_message_content)
    db.session.add(user_message)
    db.session.commit()

    # --- Сборка гибридного контекста ---
    rag_messages = vector_manager.search(chat_id, user_message_content, k=LONG_TERM_MEMORY_TOP_K)
    short_term_messages = chat.messages.order_by(Message.created_at.desc()).limit(SHORT_TERM_MEMORY_MAX_MESSAGES).all()

    # Объединение и удаление дубликатов
    combined_messages = {m.id: m for m in rag_messages}
    for m in short_term_messages: combined_messages[m.id] = m

    sorted_messages = sorted(combined_messages.values(), key=lambda m: m.created_at)
    messages_for_prompt = [{"role": m.role, "content": m.content} for m in sorted_messages]

    # Добавление системного промпта
    if chat.active_prompt:
        messages_for_prompt.insert(0, {"role": "system", "content": chat.active_prompt.content})

    # --- Вызов OpenAI ---
    response = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages_for_prompt)
    bot_message_content = response.choices[0].message.content
    bot_message = Message(chat_id=chat.id, role='assistant', content=bot_message_content)
    db.session.add(bot_message)
    db.session.commit()

    # --- Фоновое добавление в RAG ---
    Thread(target=vector_manager.add_message, args=(chat_id, user_message)).start()
    Thread(target=vector_manager.add_message, args=(chat_id, bot_message)).start()

    return jsonify(bot_message.to_dict())


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)