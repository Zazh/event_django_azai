# e2e — браузерные сценарии сайта

Текстовые сценарии (шаги и ожидания) по экранам. Пишет приёмка блока; каждая следующая
приёмка гоняет **весь** набор — это регрессия прошлых блоков. Автоматизации (Playwright) нет —
прогон руками или Claude in Chrome на dev-стеке.

| Файл | Экран | Сценарии |
|---|---|---|
| `smoke.md` | все | `addresses` |
| `layout.md` | каркас: шапка, модалка, боковое меню | `mobile-menu`, `modal-pdf-reset` |
| `home.md` | главная | `sections`, `novelties`, `directions` |
| `service.md` | страница услуги: хаб и концепции | `concept-request`, `hub-request`, `no-company` |
| `catalog.md` | страница-каталог DN Production | `catalog-request`, `sections`, `card-request`, `eurobaskets`, `admin-category` |
| `services-list.md` | список услуг | `groups` |

Имя спеки — `<файл без .md>:<сценарий>`, например `service:concept-request`: так она
называется в доках и в строке приёмки «Списано e2e: …».

## Среда

- Dev-стек из `backend/`: `docker compose up -d --build` → http://localhost:8000, база — дамп
  прода + `seed_season2027` (как развернуть — `memory/process/PROJECT.md#env` репо памяти).
- Telegram на dev заглушён: заявка создаётся, в логе `backend` — `Telegram settings not
  configured`. Без этой строки в логе формы на dev **не отправлять**.
- Админка — `/admin/`, локальные креды — `memory/secrets/dev-admin.md` репо памяти.

## Приёмы прогона

- **Тестовые заявки** — ФИО `e2e приёмка <сценарий>`, телефон `+7700000000N`. После прогона
  удалить только их: `DELETE FROM feedback_feedbackrequest WHERE full_name LIKE 'e2e приёмка%'`.
- **PDF после заявки** открывается `window.open` через 1,5 с. Проверка: новая вкладка с
  `/media/services/pdfs/…pdf`; для «PDF не открылся» — до клика обернуть `window.open` в консоли
  (`const o=window.open; window.__opened=[]; window.open=(u,t)=>{__opened.push(u); return
  o(u,t)}`) и смотреть `__opened` через 3 с после отправки.
- **Ширина 393 (телефон).** Окно Chrome уже ~500 px не сужается, а iframe с адресом сайта
  блокирует `X-Frame-Options: DENY`. Работает `srcdoc`: на любой странице сайта заменить `body`
  на `<iframe>` шириной 393 и положить в `srcdoc` HTML страницы, полученный `fetch`, с
  `<base href="http://localhost:8000/">` в `<head>`. Переходы по ссылкам внутри такого iframe
  блокируются тем же заголовком — `href` проверять, следующую страницу грузить так же.
- **Прокрутка вбок**: `document.documentElement.scrollWidth` равен ширине окна. Бегущие ленты
  (`.auto-scroll`: галерея, клиенты) шире экрана по замыслу — их обрезает `overflow-hidden`.
- **«Заявки нет»** проверять по базе, не перехватом `fetch`: GTM сам шлёт запросы.
- **Пустые карточки на скриншоте** — `loading="lazy"`: картинки грузятся при прокрутке.
- GTM вшит в `base.html` без условия — визиты dev-стенда попадают в боевую аналитику (хвост
  бэклога season-2027, до его закрытия — держать число прогонов минимальным).
