import axios from 'axios';

const apiClient = axios.create({
    baseURL: '/api', // Используем относительный путь, который будет проксироваться
    headers: {
        'Content-Type': 'application/json',
    },
});

// --- Projects API ---
export const getProjects = () => apiClient.get('/projects');
export const createProject = (name) => apiClient.post('/projects', { name });
export const renameProject = (id, name) => apiClient.put(`/projects/${id}`, { name });
export const deleteProject = (id) => apiClient.delete(`/projects/${id}`);

// --- Chats API ---
export const getChats = (projectId) => apiClient.get(`/projects/${projectId}/chats`);
export const createChat = (projectId, name) => apiClient.post(`/projects/${projectId}/chats`, { name });
export const renameChat = (id, name) => apiClient.put(`/chats/${id}`, { name });
export const deleteChat = (id) => apiClient.delete(`/chats/${id}`);

// --- Messages API ---
export const getMessages = (chatId, page = 1) => apiClient.get(`/chats/${chatId}/messages?page=${page}`);
export const sendMessage = (chatId, message) => apiClient.post(`/chats/${chatId}/messages`, { message });