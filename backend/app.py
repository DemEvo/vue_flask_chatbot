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

# 1. Инициализация и конфигурация
# ----------------------------------------------------
load_dotenv()

app = Flask(__name__)
# CORS необходим, чтобы ваш фронтенд на Vue мог общаться с бэкендом
CORS(app)

# Инициализируем клиент OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SAVE_PATH = "chat_history"
os.makedirs(SAVE_PATH, exist_ok=True) # Создаем папку, если ее нет

# Параметры нашей системы памяти
SHORT_TERM_MEMORY_MAX_MESSAGES = 4  # Храним 2 вопроса и 2 ответа
LONG_TERM_MEMORY_TOP_K = 2  # Сколько релевантных сообщений извлекать из RAG
EMBEDDING_DIMENSION = 1536  # Размерность для модели "text-embedding-ada-002"

# "База данных" в памяти для хранения сессий чата.
# В реальном проекте это была бы Redis или другая БД.
chat_sessions = {}


# 2. Функции для работы с памятью
# ----------------------------------------------------

def get_embedding(text):
    """Создает векторное представление (embedding) для текста."""
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return np.array(response.data[0].embedding)


def create_new_session(session_id):
    """Создает новую сессию чата."""
    print(f"✨ Создание новой сессии: {session_id}")
    chat_sessions[session_id] = {
        # Оперативная память: хранит последние сообщения в формате {"role": "user/assistant", "content": "..."}
        "short_term_memory": [],
        # Долговременная память:
        "vector_store": faiss.IndexFlatL2(EMBEDDING_DIMENSION),  # Векторный индекс FAISS
        "message_history": {}  # Словарь для хранения текстов сообщений по их ID в FAISS
    }


def save_session(session_id):
    if session_id in chat_sessions:
        session_data = chat_sessions[session_id]
        session_folder = os.path.join(SAVE_PATH, session_id)
        os.makedirs(session_folder, exist_ok=True)

        # Сохраняем индекс FAISS
        faiss.write_index(session_data['vector_store'], os.path.join(session_folder, 'index.faiss'))

        # Сохраняем историю сообщений
        with open(os.path.join(session_folder, 'history.json'), 'w') as f:
            # Преобразуем ключи-числа в строки для JSON
            history_to_save = {str(k): v for k, v in session_data['message_history'].items()}
            json.dump(history_to_save, f)

        # Сохраняем краткосрочную память
        with open(os.path.join(session_folder, 'short_term.json'), 'w') as f:
            json.dump(session_data['short_term_memory'], f)

        print(f"💾 Сессия {session_id} сохранена на диск.")


def load_or_create_session(session_id):
    if session_id in chat_sessions:
        return chat_sessions[session_id]

    session_folder = os.path.join(SAVE_PATH, session_id)
    index_path = os.path.join(session_folder, 'index.faiss')
    history_path = os.path.join(session_folder, 'history.json')
    short_term_path = os.path.join(session_folder, 'short_term.json')

    if os.path.exists(index_path):
        # Если файлы существуют - загружаем
        print(f"🔄 Загрузка сессии {session_id} с диска.")
        vector_store = faiss.read_index(index_path)

        with open(history_path, 'r') as f:
            # Преобразуем ключи-строки обратно в числа
            history_from_save = json.load(f)
            message_history = {int(k): v for k, v in history_from_save.items()}

        with open(short_term_path, 'r') as f:
            short_term_memory = json.load(f)

        chat_sessions[session_id] = {
            "short_term_memory": short_term_memory,
            "vector_store": vector_store,
            "message_history": message_history
        }
    else:
        # Если нет - создаем новую
        print(f"✨ Создание новой сессии: {session_id}")
        chat_sessions[session_id] = {
            "short_term_memory": [],
            "vector_store": faiss.IndexFlatL2(EMBEDDING_DIMENSION),
            "message_history": {}
        }

    return chat_sessions[session_id]


# 3. Основной API-эндпоинт
# ----------------------------------------------------
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')
    session_id = data.get('session_id')

    if not user_message or not session_id:
        return jsonify({"error": "Message and session_id are required"}), 400

    # Если сессии нет, создаем новую
    if session_id not in chat_sessions:
        create_new_session(session_id)

    session = chat_sessions[session_id]

    # --- ЛОГИКА ГИБРИДНОЙ ПАМЯТИ ---

    # 1. RAG: Поиск в долгосрочной памяти
    long_term_context = []
    if session['vector_store'].ntotal > 0:
        message_embedding = get_embedding(user_message)
        # Ищем K ближайших векторов в FAISS
        distances, indices = session['vector_store'].search(np.array([message_embedding]), LONG_TERM_MEMORY_TOP_K)

        # Извлекаем тексты найденных сообщений
        for idx in indices[0]:
            if idx in session['message_history']:  # Убедимся, что индекс валиден
                long_term_context.append(session['message_history'][idx])

    rag_context_str = "\n".join([f"- {msg['content']}" for msg in long_term_context])

    # 2. Формируем финальный промпт для модели
    messages_for_prompt = []

    # Системный промпт, объясняющий модели, как использовать контекст
    system_prompt = f"""Ты - полезный ассистент. У тебя есть два типа памяти для ответа на вопрос пользователя.

1.  **Контекст из долгосрочной памяти (наиболее релевантные прошлые сообщения):**
    {rag_context_str if rag_context_str else "Пока нет релевантных сообщений в долгосрочной памяти."}

2.  **Краткосрочная память (последние несколько сообщений диалога):**
    Ниже будет история последних сообщений.

Основываясь на ОБОИХ типах памяти, дай наилучший ответ на последний вопрос пользователя.
"""
    messages_for_prompt.append({"role": "system", "content": system_prompt})

    # Добавляем краткосрочную память
    messages_for_prompt.extend(session['short_term_memory'])

    # Добавляем текущее сообщение пользователя
    messages_for_prompt.append({"role": "user", "content": user_message})

    # 3. Вызов модели OpenAI
    response = client.chat.completions.create(
        model="gpt-5",
        messages=messages_for_prompt
    )
    bot_message = response.choices[0].message.content

    # 4. Обновление систем памяти
    # Добавляем текущий вопрос и ответ в краткосрочную память
    session['short_term_memory'].append({"role": "user", "content": user_message})
    session['short_term_memory'].append({"role": "assistant", "content": bot_message})

    # Если краткосрочная память переполнена, старейшие сообщения уходят в долгосрочную
    while len(session['short_term_memory']) > SHORT_TERM_MEMORY_MAX_MESSAGES:
        message_to_archive = session['short_term_memory'].pop(0)  # Берем самое старое сообщение

        # Добавляем его в RAG
        message_embedding = get_embedding(message_to_archive['content'])
        current_index = session['vector_store'].ntotal
        session['vector_store'].add(np.array([message_embedding]))
        session['message_history'][current_index] = message_to_archive
        print(f"📝 Архивировано в RAG: '{message_to_archive['content'][:30]}...'")

    return jsonify({"reply": bot_message})


if __name__ == '__main__':
    app.run(debug=True, port=5000)