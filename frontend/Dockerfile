# --- СТАДИЯ СБОРКИ (BUILD) ---
FROM node:18-alpine AS builder

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем package.json и устанавливаем зависимости
COPY package*.json ./
RUN npm install

# Копируем остальные файлы приложения
COPY . .

# Собираем приложение для продакшена
RUN npm run build

# --- СТАДИЯ РАБОТЫ (SERVE) ---
FROM nginx:1.25-alpine

# Копируем собранные статические файлы из стадии "builder" в папку Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Копируем наш кастомный конфиг для Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Открываем порт 80
EXPOSE 80

# Запускаем Nginx
CMD ["nginx", "-g", "daemon off;"]