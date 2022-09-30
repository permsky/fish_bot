# Магазин по торговле морепродуктами.

Репозиторий содержит скрипт для запуска Telegram-бота, с помощью которого можно оформить заказ в магазине морепродуктов. Бот взаимодействует с [CMS магазина Elasticpath](https://euwest.cm.elasticpath.com/) посредством [Moltin API](https://documentation.elasticpath.com/commerce-cloud/docs/api/index.html).

Работа Telegram-бота:

![](screencasts/tg_bot.gif)

Также можно протестировать работу бота самому: 
  - [Telegram-бот](https://t.me/AgileMenuBot)

## Запуск

- Скачайте код
- Настройте окружение. Для этого выполните следующие действия:
  - установите Python3.x;
  - создайте виртуальное окружение [virtualenv/venv](https://docs.python.org/3/library/venv.html) для изоляции проекта и активируйте его.
  - установите необходимые зависимости:

    ```
    pip install -r requirements.txt
    ```
- Создайте Telegram-бота и получите токен. Воспользуйтесь услугами [BotFather](https://telegram.me/BotFather), для этого необходимо ввести `/start` и следовать инструкции.
- В директории со скриптами создайте файл `.env`, в котором будут храниться чувствительные данные:
    ```
    TG_BOT_TOKEN='токен telegram-бота'
    CLIENT_ID='id клиента Moltin API'
    CLIENT_SECRET='пароль клиента Moltin API'
    DB_HOST='адрес хоста базы данных redis'
    DB_PORT='порт хоста базы данных redis'
    DB_PASSWORD='пароль хоста базы данных redis'
    ```
- запустите  Telegram-бота командой:
    ```
    python main.py
    ```

## Деплой ботов на [Heroku](https://id.heroku.com/login)

- Разместите код в своем репозитории на GitHub.
- Зарегистрируйтесь на Heroku и создайте приложение во вкладке `Deploy`.
- Сохраните чувствительные данные во вкладке `Settings` в `Config Vars`.
- Выберите ветку `main` нажмите `Deploy Branch` во вкладке `Deploy`.
- Активируйте процессы на вкладке `Resources`.
Для просмотра в консоли возможных ошибок при деплое используйте [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli#download-and-install).

## Цели проекта
Код написан в учебных целях — это урок в курсе по Python и веб-разработке на сайте [Devman](https://dvmn.org).