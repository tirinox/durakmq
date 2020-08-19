# durakmq

Сетевая игра в карты "Дурак". Для GUI использован Kivy.

![](screenshot.jpg)

## Запуск на Android

[Установка Buildozer](https://kivy.org/doc/stable/guide/packaging-android.html)

Если у вас Mac OS, то выполните из терминала команды (можно из Terminal из PyCharm):

```pip install Cython
git clone https://github.com/kivy/buildozer.git
cd buildozer
sudo python setup.py install
```

Подключи устройство и разреши отладку по USB

Установка и запуск приложения на Android устройстве:

```buildozer android debug deploy run```

Если что-то не работает, то следует изучить логи на устройстве. Для этого есть команда:

```adb logcat -T 1 python:D "*:S"```

Она фильтрует с устройства только те логи, которые относятся к Kivy.

## ToDo

1. Перевод карты
2. Выбор, что отбить данной картой
3. Не скрывать козырь, если взяли - сделать его полупрозрачным
4. Последнюю карту из колоды не убирать вправо, а дать ее в руку
5. Подбросить карты, если сопрерник берет