import telebot
import requests
import time
import json
import os
from urllib.parse import quote
from bs4 import BeautifulSoup

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

FAVORITES_FILE = 'favorites.json'
search_results = {}  # Временное хранилище результатов поиска


def load_favorites():
    if os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_favorites(favorites):
    with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
        json.dump(favorites, f, ensure_ascii=False, indent=2)


def search_movie(movie_name):
    search_url = f"https://v4.fanfilm4k.media/index.php?do=search&subaction=search&story={quote(movie_name)}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        movie_cards = soup.find_all('article', class_='card')
        movies = []

        for card in movie_cards[:10]:
            link_tag = card.find('a', href=True)
            if link_tag:
                link = link_tag.get('href')
                if not link.startswith('http'):
                    link = 'https://v4.fanfilm4k.media' + link

                img_tag = card.find('img')
                title = ''
                poster = None

                if img_tag:
                    if img_tag.get('alt'):
                        title = img_tag.get('alt').replace(' постер 4К', '').strip()
                    if img_tag.get('src'):
                        poster = img_tag.get('src')
                        if not poster.startswith('http'):
                            poster = 'https://v4.fanfilm4k.media' + poster

                if title:
                    movies.append({'title': title, 'link': link, 'poster': poster})
        return movies
    except Exception as e:
        print(f"Ошибка: {e}")
        return []


def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = telebot.types.KeyboardButton("🔍 Поиск фильма")
    btn2 = telebot.types.KeyboardButton("❤️ Избранное")
    btn3 = telebot.types.KeyboardButton("❓ Помощь")
    btn4 = telebot.types.KeyboardButton("🗑 Очистить избранное")
    markup.add(btn1, btn2, btn3, btn4)
    return markup


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(
        message.chat.id,
        "🎬 Привет! Я бот для поиска фильмов\n\n"
        "Используй кнопки ниже или введи название фильма",
        reply_markup=main_menu()
    )


@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(
        message.chat.id,
        "📖 Команды:\n"
        "/start - главное меню\n"
        "/favorites - избранное\n"
        "/clear_favorites - очистить избранное",
        reply_markup=main_menu()
    )


@bot.message_handler(commands=['favorites'])
def show_favorites(message):
    favorites = load_favorites()
    user_id = str(message.chat.id)

    if user_id in favorites and favorites[user_id]:
        bot.send_message(message.chat.id, f"❤️ Твои избранные фильмы ({len(favorites[user_id])}):")
        for i, movie in enumerate(favorites[user_id], 1):
            caption = f"{i}. 📺 {movie['title']}\n🔗 {movie['link']}"
            if movie.get('poster'):
                try:
                    bot.send_photo(message.chat.id, movie['poster'], caption=caption)
                except:
                    bot.send_message(message.chat.id, caption)
            else:
                bot.send_message(message.chat.id, caption)
            time.sleep(0.3)
    else:
        bot.send_message(message.chat.id, "❤️ У тебя пока нет избранных фильмов", reply_markup=main_menu())


@bot.message_handler(commands=['clear_favorites'])
def clear_favorites(message):
    favorites = load_favorites()
    user_id = str(message.chat.id)
    favorites[user_id] = []
    save_favorites(favorites)
    bot.send_message(message.chat.id, "🗑 Избранное очищено", reply_markup=main_menu())


@bot.message_handler(content_types=['text'])
def handle_message(message):
    user_text = message.text.strip()

    if user_text == "🔍 Поиск фильма":
        bot.send_message(message.chat.id, "Введи название фильма для поиска:", reply_markup=main_menu())
        return
    elif user_text == "❤️ Избранное":
        show_favorites(message)
        return
    elif user_text == "❓ Помощь":
        help_message(message)
        return
    elif user_text == "🗑 Очистить избранное":
        clear_favorites(message)
        return

    if user_text.startswith('/'):
        return

    status_msg = bot.send_message(message.chat.id, f"🔍 Ищу '{user_text}'...")
    movies = search_movie(user_text)
    bot.delete_message(message.chat.id, status_msg.message_id)

    if movies:
        # Сохраняем результаты поиска
        chat_id = str(message.chat.id)
        search_results[chat_id] = movies

        bot.send_message(message.chat.id, f"🎬 Найдено {len(movies)} фильмов:")

        for i, movie in enumerate(movies, 1):
            caption = f"{i}. 📺 {movie['title']}\n🔗 {movie['link']}"

            markup = telebot.types.InlineKeyboardMarkup()
            # Используем простой ID без спецсимволов
            btn = telebot.types.InlineKeyboardButton("❤️ В избранное", callback_data=f"fav_{chat_id}_{i}")
            markup.add(btn)

            if movie['poster']:
                try:
                    bot.send_photo(message.chat.id, movie['poster'], caption=caption, reply_markup=markup)
                except:
                    bot.send_message(message.chat.id, caption, reply_markup=markup)
            else:
                bot.send_message(message.chat.id, caption, reply_markup=markup)
            time.sleep(0.3)
    else:
        bot.send_message(message.chat.id, f"😕 Фильм '{user_text}' не найден", reply_markup=main_menu())


@bot.callback_query_handler(func=lambda call: call.data.startswith('fav_'))
def handle_favorite(call):
    try:
        _, chat_id, movie_id = call.data.split('_')
        movie_id = int(movie_id) - 1

        if chat_id in search_results and movie_id < len(search_results[chat_id]):
            movie = search_results[chat_id][movie_id]

            favorites = load_favorites()
            user_id = str(call.from_user.id)

            if user_id not in favorites:
                favorites[user_id] = []

            exists = any(m['link'] == movie['link'] for m in favorites[user_id])

            if not exists:
                favorites[user_id].append({
                    'title': movie['title'],
                    'link': movie['link'],
                    'poster': movie.get('poster', '')
                })
                save_favorites(favorites)
                bot.answer_callback_query(call.id, f"✅ {movie['title']} добавлен в избранное!")
            else:
                bot.answer_callback_query(call.id, f"⚠️ {movie['title']} уже в избранном")
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка: фильм не найден")
    except Exception as e:
        print(f"Ошибка в callback: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка")


if __name__ == '__main__':
    print("🤖 Бот запущен...  / тестовое изменение")
    try:
        bot.polling(non_stop=True, interval=1, timeout=20)
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(5)