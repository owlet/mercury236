## Работа с прибором учета электроэнергии Меркурий 236 / Mercury 236

- Для работы необходимо физическое подключение к прибору учета по интерфейсу RS-485.

## Установка

1. Склонируйте репозиторий
2. Установите pyserial: ```pip3 install pyserial```
3. Запустите: ```python3 energymeter.py```

## Help
```python3 energymeter.py --help```
```
  --port PORT           Серийный порт (default: /dev/ttyUSB0)
  --baudrate BAUDRATE   Baud rate (default: 9600)
  --parity {N,E,O}      Чётность (N-none, E-even, O-odd, default: N)
  --bytesize {5,6,7,8}  Data bits (default: 8)
  --stopbits {1,2}      Stop bits (default: 1)
  --timeout TIMEOUT     Тайм-аут ожидания подключения в секундах (default: 1.0)
```

## Известные проблемы
- Не читает частоту сети
