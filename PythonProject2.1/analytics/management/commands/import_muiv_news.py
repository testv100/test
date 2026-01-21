import re
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_date

from analytics.models import News

FEED_URL = "https://www.muiv.ru/about/news/"
BASE = "https://www.muiv.ru"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)

def _abs_url(href: str) -> str:
    href = (href or "").strip()
    if not href:
        return ""
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return BASE + href
    if href.startswith("http"):
        return href
    return ""

def _extract_article_links(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.select("a[href]"):
        url = _abs_url(a.get("href"))
        if not url:
            continue

        # Берем только статьи новостей MUIV
        # Пример: https://www.muiv.ru/about/news/innovatsii-v-obuchenii-student/
        if "/about/news/" in url:
            # отбрасываем сам список /about/news/ и оставляем страницы-статьи
            path = url.split("?", 1)[0].split("#", 1)[0]
            if path.rstrip("/") == FEED_URL.rstrip("/"):
                continue
            # у статьи обычно есть slug после /about/news/
            if re.match(r"^https://www\.muiv\.ru/about/news/[^/]+/?$", path):
                links.append(path.rstrip("/") + "/")

    # уникальные, в порядке появления
    return list(dict.fromkeys(links))

def _parse_article(url: str) -> dict:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    # title
    h1 = soup.find("h1")
    title = h1.get_text(" ", strip=True) if h1 else "Новость МУИВ"

    # date: часто на странице есть dd.mm.yyyy
    text_all = soup.get_text(" ", strip=True)
    dt = timezone.now()
    m = re.search(r"(\d{2}\.\d{2}\.\d{4})", text_all)
    if m:
        dmy = m.group(1)
        d = parse_date(f"{dmy[6:10]}-{dmy[3:5]}-{dmy[0:2]}")
        if d:
            dt = timezone.make_aware(timezone.datetime(d.year, d.month, d.day))

    # content: берем основной текст
    container = soup.find("article") or soup.find("main") or soup.body
    parts = []
    for p in container.find_all(["p", "li"]):
        t = p.get_text(" ", strip=True)
        if t and len(t) > 20:
            parts.append(t)
    body = "\n\n".join(parts).strip()
    if not body:
        body = text_all[:3000]

    return {"title": title[:200], "body": body, "created_at": dt}

class Command(BaseCommand):
    help = "Import MUIV news from https://www.muiv.ru/about/news/ using Playwright (for list) + requests (for articles)"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20, help="how many news to import")
        parser.add_argument("--pages", type=int, default=3, help="how many listing pages to scan (best-effort)")

    def handle(self, *args, **opts):
        limit = int(opts["limit"])
        pages = int(opts["pages"])

        # 1) Получаем HTML списка через Playwright (как браузер)
        from playwright.sync_api import sync_playwright

        listing_html = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=UA)
            page.goto(FEED_URL, wait_until="networkidle", timeout=60000)
            listing_html.append(page.content())

            # 2) пробуем собрать доп. страницы (если есть пагинация)
            # ищем ссылки вида ?PAGEN_1=2 и открываем несколько
            soup = BeautifulSoup(listing_html[0], "lxml")
            pagelinks = []
            for a in soup.select("a[href*='PAGEN_']"):
                u = _abs_url(a.get("href"))
                if u:
                    pagelinks.append(u)

            pagelinks = list(dict.fromkeys(pagelinks))[: max(0, pages - 1)]

            for u in pagelinks:
                try:
                    page.goto(u, wait_until="networkidle", timeout=60000)
                    listing_html.append(page.content())
                except Exception:
                    pass

            browser.close()

        # 3) соберем ссылки на статьи
        links = []
        for html in listing_html:
            links.extend(_extract_article_links(html))
        links = list(dict.fromkeys(links))[:limit]

        created = 0
        updated = 0

        for url in links:
            try:
                data = _parse_article(url)
                obj, was_created = News.objects.get_or_create(
                    source_url=url,
                    defaults={
                        "title": data["title"],
                        "body": data["body"],
                        "created_at": data["created_at"],
                        "is_published": True,
                        "source": "muiv",
                    }
                )
                if was_created:
                    created += 1
                else:
                    # можно обновлять текст/заголовок
                    if obj.title != data["title"] or obj.body != data["body"]:
                        obj.title = data["title"]
                        obj.body = data["body"]
                        obj.save(update_fields=["title", "body"])
                        updated += 1

            except Exception as e:
                self.stderr.write(f"Skip {url}: {e}")

        self.stdout.write(self.style.SUCCESS(
            f"MUIV import done. scanned={len(links)} created={created} updated={updated}"
        ))
