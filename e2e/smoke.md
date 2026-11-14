# smoke — адреса сайта

## addresses — старые и новые адреса отдают 200

С блока 1 season-2027 (Р-14: адреса существующих страниц не меняются).

Шаги (`curl -s -o /dev/null -w '%{http_code}' http://localhost:8000<адрес>`):

1. Старые: `/`, `/services/`, `/contacts/`, `/admin/login/`,
   `/services/korporativnye-vecherinki-pod-klyuch/`, `/services/korporativy-i-timbildingi/`,
   `/services/detskie-novogodnie-utrenniki/`, `/services/detskie-novogodnie-podarki/`.
2. Новые (блок 1): `/services/legends/`, `/services/teleport-2037/`,
   `/services/immersive-show/`; (блок 2): `/services/korporativnye-podarki/`,
   `/services/korporativnaya-odezhda-i-specodezhda/`,
   `/services/brendirovannaya-produkciya-i-snabzhenie-ofisa/`.
3. Несуществующий: `/services/nonexistent/`.
4. Со всех страниц шагов 1–2 собрать адреса `/media/…` и `/static/…` (включая те, что лежат в
   JS галерей) и запросить каждый.
5. `og:image` главной: `curl -s localhost:8000/ | grep og:image` — адрес с `/static/`.

Ожидание: шаги 1–2 — 200; шаг 3 — 404; шаг 4 — все 200; шаг 5 — путь `/static/…` отдаёт 200.
