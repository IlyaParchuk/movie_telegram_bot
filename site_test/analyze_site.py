import requests
from bs4 import BeautifulSoup

def analyze_site():
    print("Начинаем анализ сайта...")

    url = "https://v4.fanfilm4k.media/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        print(f"Статус ответа: {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")

        with open('site_structure.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())

            print("✅ HTML страницы сохранен в файл 'site_structure.html'")
            print("📁 Открой этот файл в браузере или текстовом редакторе")

            print("\nПервые 500 символов страницы")
            print("-"*50)
            print(response.text[:500])
            print("-"*50)

        possible_classes = ['post', 'movie', 'film', 'item', 'article']

        print("\n🔍 Ищем возможные контейнеры фильмов:")
        for class_name in possible_classes:
            elements = soup.find_all(class_=class_name)
            if elements:
                print(f"  - Найдено {len(elements)} элементов с классом '{class_name}'")

    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    analyze_site()