# Xpert: установка одним скриптом

## Быстрый старт

```bash
git clone https://github.com/mybrohigh/Xpert-VPS.git Xpert
cd Xpert
sudo bash scripts/install.sh install --service-name xpert --install-dir /opt/xpert
```

Что делает скрипт:
- подготавливает Python-окружение (`.venv`) и ставит backend-зависимости;
- выполняет `alembic upgrade head`;
- собирает dashboard (`npm ci`, `npm run build`, `dist -> build`);
- создаёт и перезапускает systemd сервис (`xpert.service`).

## Команды после установки

```bash
sudo systemctl status xpert
sudo journalctl -u xpert -n 120 --no-pager
```

Панель обычно доступна по:

```text
http://SERVER_IP:8000/dashboard/
```

## Полезные опции install-скрипта

```bash
# Пропустить frontend сборку
sudo bash scripts/install.sh install --skip-frontend

# Пропустить создание systemd сервиса
sudo bash scripts/install.sh install --skip-systemd

# Указать другое имя сервиса
sudo bash scripts/install.sh install --service-name xpert
```

## Аудит дубликатов (без удаления)

```bash
bash scripts/audit_duplicates.sh
```

Отчёт сохраняется в `reports/duplicate_audit_*.txt`.
