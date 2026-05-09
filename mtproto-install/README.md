# Свой MTProto-прокси за 1 минуту

Скрипт разворачивает личный прокси для Telegram на вашем VPS. В конце выдаёт ссылку вида `tg://proxy?...` — просто нажимаете и подключаетесь.

## Что нужно

- VPS с Ubuntu или Debian (x86_64)
- Root-доступ
- 5 минут времени

## Установка

Одна команда — и всё готово:

```bash
curl -fsSL https://raw.githubusercontent.com/vasneverov/mtproto-install/main/install-mtproto.sh | sudo bash
```

В конце скрипт напечатает что-то вроде:

```
┌─────────────────────────────────────────┐
│  Server IP:   1.2.3.4                   │
│  Port:        5349                      │
│  Secret:      ee9f3b...                 │
│  tg://proxy?server=1.2.3.4&port=...     │
└─────────────────────────────────────────┘
```

Эту ссылку открываете в Telegram — прокси добавляется автоматически.

## Хочу другой порт или домен

По умолчанию используется порт `5349` и домен `dl.google.com` (под него маскируется трафик). Можно указать свои:

```bash
curl -fsSL https://raw.githubusercontent.com/vasneverov/mtproto-install/main/install-mtproto.sh | sudo bash -s -- www.apple.com 8443
```

Первый аргумент — домен, второй — порт.

## Управление

```bash
systemctl status mtg      # работает или нет
systemctl restart mtg     # перезапустить
journalctl -u mtg -f      # смотреть логи
```

## Важно

Ссылку `tg://proxy?...` никому не публикуйте в открытом доступе — любой, у кого она есть, сможет использовать ваш прокси.

---

Использует [mtg v2.2.3](https://github.com/9seconds/mtg).
