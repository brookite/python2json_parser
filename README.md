## Проект генерации кода  алгоритма на языках программирования в HTML

Проект состоит из модуля генерации универсального дерева алгоритма в формате JSON и модуля рендеринга алгоритма в HTML с кнопками действия. 

Поддерживаемые алгоритмические структуры:
- Следование (с учетом вызова функций)
- Ветвление
- Цикл "для"
- Цикл "пока"
- Функция

Поддерживаемые языки программирования: Python

### Установка
```commandline
python -m pip install -r requirements.txt
```

### Запуск

#### Генерация дерева:
```commandline
python code2json/main.py LANG PATH_TO_SOURCE_CODE
```

Пример:

```commandline
python code2json/main.py python /home/abc/1.py > result.json
```

#### Создание HTML из дерева:
```commandline
python json2html/main.py LANG PATH_TO_TREE
```
Флаг --disable-buttons отключает кнопки действий

Пример:

```commandline
python json2html/main.py python /home/abc/result.json > result.html
```