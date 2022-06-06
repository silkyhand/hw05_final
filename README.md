# Социальная сеть YaTube.
Социальная сеть с возможностью создания, просмотра, редактирования и удаления (CRUD) записей. Реализован механизм подписки на понравившихся авторов и отслеживание их записей. Покрытие тестами. Возможность добавления изображений.

## Технологии

- Django 2.2
- Python 3.7
- Django Unittest
- Django debug toolbar
- PostgreSQL
- Django ORM

## Запуск проекта в dev-режиме:
Клонируйте репозиторий:
```sh
https://github.com/silkyhand/hw05_final.git
```
Cоздайте и активируйте виртуальное окружение:
```sh
python -m venv venv
```
```
source venv/Scripts/activate
```
Установите зависимости:
```sh
pip install -r requirements.txt
```
Примените миграции:
```sh
python manage.py makemigrations
```
```
python manage.py migrate
```
Создайте администратора:
```sh
python manage.py createsuperuser
```
Запустите приложение:
```sh
python manage.py runserver
```
## License
MIT Free Software
