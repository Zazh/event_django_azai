# deploy/ — прод-конфиги (без секретов)

Копии файлов с сервера `ubuntu@195.210.47.4` один к одному: сверка дрейфа —
`ssh ubuntu@195.210.47.4 cat <путь на сервере> | diff - deploy/<файл>`. Исключение до релиза
season-2027: `Dockerfile` здесь уже берёт `core/requirements.txt` — на сервер он встаёт шагом 3
ранбука (репо памяти, `process/PROJECT.md#deploy`); до того `diff` покажет строку `COPY`.

| Файл здесь | Путь на сервере |
|---|---|
| `docker-compose.yml` | `/home/ubuntu/docker-compose.yml` |
| `nginx/conf.d/default.conf` | `/home/ubuntu/nginx/conf.d/default.conf` |
| `Dockerfile` | `/home/ubuntu/brandsite/Dockerfile` (контекст сборки — `/home/ubuntu/brandsite/`) |

- Секреты — только на сервере: `/home/ubuntu/.env` (`POSTGRES_*` для сервиса `db`) и
  `/home/ubuntu/brandsite/.env` (переменные Django, `env_file` сервиса `backend`). Сюда — только
  имена переменных.
- Код смонтирован в `backend` томом (`./brandsite/core:/app` — git-клон этого репо, ветка
  `main`); при каждом старте контейнера выполняются `migrate` и `collectstatic`. Образ держит
  только зависимости.
- Правка конфига — сначала на сервере, затем копия сюда тем же коммитом, что и запись в
  процедуре выката.
