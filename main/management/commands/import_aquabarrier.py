# main/management/commands/import_aquabarrier_catalog.py
import re
import time
from decimal import Decimal
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from main.models import Category, Product, Variant

BASE_URL = "http://www.aquabarrier.ru"
CATEGORY_URL = "http://www.aquabarrier.ru/content/blogcategory/16/83/"

# --- настройки ---
REQUEST_TIMEOUT = 15
PAUSE_SEC = 0.5
USER_AGENT = "Mozilla/5.0 (compatible; ImportBot/1.0; +https://example.local/)"

# --- вспомогалки ---
def clean(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip())

def parse_price(text: str):
    if not text:
        return None
    text = text.replace("\xa0", "").replace(" ", "")
    m = re.search(r"(\d{3,}|\d+)", text)  # предпочитаем большие числа, но допустим и любые
    if not m:
        return None
    try:
        return Decimal(re.sub(r"[^\d]", "", m.group(1)))
    except Exception:
        return None

def find_product_tables(soup):
    """Возвращает список <table> которые похожи на таблицы вариантов"""
    tables = soup.find_all("table")
    good = []
    for t in tables:
        # простая эвристика: в таблице должно быть >1 строки и >1 столбца
        rows = t.find_all("tr")
        if len(rows) < 2:
            continue
        cols0 = rows[0].find_all(["td", "th"])
        if len(cols0) < 2:
            continue
        good.append(t)
    return good

def parse_table_to_variants(table):
    """Универсальный (тяжёлый) парсер таблицы → список словарей"""
    rows = table.find_all("tr")
    if not rows or len(rows) < 1:
        return []

    # заголовки из первой строки
    header_cells = rows[0].find_all(["th", "td"])
    headers = [clean(c.get_text()).lower() for c in header_cells]

    def idx_by_keywords(words):
        for i, h in enumerate(headers):
            for w in words:
                if w in h:
                    return i
        return None

    idx_name = idx_by_keywords(["наимен", "тип", "обознач", "модель"]) or 0
    idx_move = idx_by_keywords(["перемещ", "ход", "movement"])
    idx_load = idx_by_keywords(["нагруз", "mpa", "прочн"])
    idx_a = idx_by_keywords(["a", "ширин", "размер a"])
    idx_b = idx_by_keywords(["b", "размер b"])
    idx_c = idx_by_keywords(["c", "высот", "высота", "размер c"])
    idx_comp = idx_by_keywords(["компенс"])
    idx_price = idx_by_keywords(["цен", "руб", "₸", "тг", "price"])

    variants = []
    data_rows = rows[1:]  # предполагаем, что первая — заголовок
    for row in data_rows:
        cols = [clean(c.get_text()) for c in row.find_all(["td", "th"])]
        if not cols:
            continue

        def g(i):
            if i is None or i >= len(cols):
                return ""
            return cols[i]

        name = g(idx_name) or g(0)
        if not name or len(name) < 1:
            continue

        variant = {
            "name": name,
            "movement": g(idx_move),
            "load_mpa": g(idx_load),
            "size_a": g(idx_a),
            "size_b": g(idx_b),
            "size_c": g(idx_c),
            "compensator": g(idx_comp),
            "price": parse_price(g(idx_price)),
        }
        variants.append(variant)

    return variants

# --- команда ---
class Command(BaseCommand):
    help = "Импорт только каталога деформационных швов с aquabarrier.ru (только каталожные страницы)"

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=0, help='Ограничить число страниц (0=все)')
        parser.add_argument('--start', type=int, default=0, help='Пропустить первые N страниц (для возобновления)')
        parser.add_argument('--clear', action='store_true', help='Удалить все Products и Variants в категории перед импортом')
        parser.add_argument('--dry-run', action='store_true', help='Только вывести что бы импортировалось, без записи в БД')

    def handle(self, *args, **options):
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})

        # Создаём категорию (если нет)
        category, _ = Category.objects.get_or_create(
            slug="deformacionnye-shvy",
            defaults={"name": "Деформационные швы"}
        )

        if options['clear']:
            self.stdout.write(self.style.WARNING("Удаляю старые продукты и варианты в категории..."))
            # удаляем продукты этой категории (и связанные варианты благодаря on_delete)
            Product.objects.filter(category=category).delete()
            self.stdout.write(self.style.SUCCESS("Удаление завершено."))

        # Получаем список ссылок
        self.stdout.write("Загружаю страницу категории...")
        try:
            r = session.get(CATEGORY_URL, timeout=REQUEST_TIMEOUT)
            r.encoding = "cp1251"  # сайт в cp1251
        except Exception as e:
            self.stderr.write(f"Ошибка при загрузке категории: {e}")
            return

        soup = BeautifulSoup(r.text, "html.parser")

        # Сбор ссылок — только те, которые соответствуют /content/view/<digits>/<digits>/
        raw_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if "/content/view/" in href:
                full = urljoin(BASE_URL, href)
                raw_links.append(full)

        # Уникализируем и отфильтруем по шаблону
        re_prod = re.compile(r"/content/view/\d+/\d+/?$")
        links = []
        for u in raw_links:
            if re_prod.search(u):
                if u not in links:
                    links.append(u)

        self.stdout.write(self.style.SUCCESS(f"Найдено ссылок с шаблоном /content/view/: {len(links)}"))

        # применим start/limit
        start = options.get('start', 0) or 0
        limit = options.get('limit', 0) or 0
        links = links[start:]
        if limit:
            links = links[:limit]
        self.stdout.write(f"Будем обрабатывать: {len(links)} страниц (start={start}, limit={limit})")

        dry = options.get('dry_run', False)

        processed = 0
        for idx, url in enumerate(links, start=1):
            self.stdout.write(f"\n[{idx}] Загружаю {url} ...")
            try:
                r = session.get(url, timeout=REQUEST_TIMEOUT)
                r.encoding = "cp1251"
            except Exception as e:
                self.stderr.write(f"  Ошибка загрузки {url}: {e}")
                continue

            page_soup = BeautifulSoup(r.text, "html.parser")

            # Быстрая эвристика: пропускаем страницы, которые явно не каталог (нет таблиц и нет ключевых слов)
            txt = page_soup.get_text(separator=" ").lower()
            if ("размер" not in txt and "характ" not in txt and "перемещ" not in txt and not page_soup.find("table")):
                self.stdout.write(self.style.NOTICE("  Пропускаем — похоже не каталожная страница (нет таблицы и ключевых слов)."))
                continue

            # title
            title_tag = page_soup.find("h1") or page_soup.find("h2")
            title = clean(title_tag.get_text()) if title_tag else f"Тип шва {idx}"

            # маленькая защита от мусора/кракозябр
            if len(title) > 250 or re.search(r'[^\x00-\x7f]+', title) and len(title) > 2000:
                self.stdout.write(self.style.WARNING("  Пропускаем страницу — подозрительно длинный или повреждённый заголовок."))
                continue

            # Описание: возьмём div.content без таблиц
            desc = ""
            content_block = page_soup.find("div", class_="content") or page_soup.find("article") or page_soup.find("div", id="content")
            if content_block:
                # удалим таблицы из описания
                for t in content_block.find_all("table"):
                    t.decompose()
                desc = clean(content_block.get_text())[:4000]
            else:
                # fallback: несколько первых параграфов
                paras = page_soup.find_all("p")
                if paras:
                    desc = clean(" ".join([p.get_text() for p in paras[:5]]))[:4000]

            # Таблицы вариантов (только «каталожные» таблицы)
            tables = find_product_tables(page_soup)
            if not tables:
                self.stdout.write(self.style.NOTICE("  Таблицы не найдены — пропускаем страницу."))
                continue

            # Если dry-run — только печатаем что нашли
            if dry:
                self.stdout.write(self.style.NOTICE(f"  DRY RUN: найдены {len(tables)} таблиц на странице. title: {title}"))
                processed += 1
                time.sleep(PAUSE_SEC)
                continue

            # Создаём/обновляем продукт
            slug_candidate = slugify(title)[:200]
            product, created = Product.objects.get_or_create(
                slug=slug_candidate,
                defaults={"category": category, "name": title, "description": desc}
            )
            if not created:
                # обновляем поля при необходимости
                changed = False
                if desc and product.description != desc:
                    product.description = desc
                    changed = True
                if product.name != title:
                    product.name = title
                    changed = True
                if changed:
                    product.save()
                    self.stdout.write(self.style.SUCCESS("  Обновлён продукт"))
            else:
                self.stdout.write(self.style.SUCCESS("  Создан продукт"))

            # Обходим таблицы и создаём/обновляем варианты
            total_variants = 0
            for table in tables:
                variants = parse_table_to_variants(table)
                for order_idx, v in enumerate(variants):
                    vname = v.get("name") or f"Вариант {order_idx+1}"
                    defaults = {
                        "movement": v.get("movement", "") or "",
                        "load_mpa": v.get("load_mpa", "") or "",
                        "size_a": v.get("size_a", "") or "",
                        "size_b": v.get("size_b", "") or "",
                        "size_c": v.get("size_c", "") or "",
                        "compensator": v.get("compensator", "") or "",
                        "order": order_idx,
                    }
                    if v.get("price") is not None:
                        defaults["price"] = v.get("price")
                    Variant.objects.update_or_create(product=product, name=vname, defaults=defaults)
                    total_variants += 1

            self.stdout.write(self.style.SUCCESS(f"  Обработано вариантов: {total_variants}"))
            processed += 1
            time.sleep(PAUSE_SEC)

        self.stdout.write(self.style.SUCCESS(f"\nГотово. Импортировано страниц: {processed}"))