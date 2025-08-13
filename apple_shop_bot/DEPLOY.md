## Деплой

### Вариант A: Docker Compose
1) Скопируйте `.env.example` → `.env` и задайте `BOT_TOKEN` (и при желании `OWNER_CHAT_ID`)
2) Соберите и запустите:
```bash
docker compose build
docker compose up -d
```
3) Логи: `docker compose logs -f`

### Вариант B: systemd (Linux)
1) Скопируйте `.env.example` → `.env` и задайте `BOT_TOKEN`
2) Скопируйте юнит:
```bash
sudo cp deploy/apple_shop_bot.service /etc/systemd/system/apple_shop_bot.service
```
3) Перезапустите systemd и включите сервис:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now apple_shop_bot
```
4) Логи: `journalctl -u apple_shop_bot -f`

### Вариант C: Локально (polling)
```bash
export BOT_TOKEN=XXX
python main.py
```