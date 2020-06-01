disqus: https-mqb-readthedocs-io
# Настройка профилей шин

### Настройка системы контроля давления в шинах через Individual профиль

!!! tip
    В старых версиях OBD11 был перепутан перевод (обычный - полный)
    
Настройки для обычной нагрузки

    Блок 65 → Адаптация

    > НОМ. давление для передней оси, обычный
    Старое значение: 255
    Новое значение: 22 (если нужно 2.2 бара)
    → Применить
    
    > НОМ. давление для задней оси, обычный
    Старое значение: 255
    Новое значение: 22 (если нужно 2.2 бара)
    → Применить

Настройки для полной нагрузки

    > НОМ. давление Полная загрузка передней оси
    Старое значение: 255
    Новое значение: 26 (если нужно 2.6 бара)
    → Применить
    
    > НОМ. давление Полная загрузка задней оси
    Старое значение: 255
    Новое значение: 26 (если нужно 2.6 бара)
    → Применить

### Создание собственно профиля шин

+ [Online генератор TMPS](/MQB/tiresCoding)

Поддерживающиеся блоки:   
3AA907273D; 3AA907273F; 3AA907273H; 5Q0907273; 5Q0907273B; 7P6907273H; 7P6907273L.

Для генерации необходимо выбрать нужный формат (какой утилитой будет проводиться загрузка) и правильный блок шин. 
Потом надо создать/наполнить таблицу давлений для него. 
В качестве названий может быть что угодно - размерность шин, названия Winter-Summer и т.д. Но все названия должны быть только на латинице!

Готовый файл заливается с помощью ODIS E или VCDS в блок 65:

> Diagnostic function - Write Data Record

![Screenshot](../images/MQB/odis-e-tires.png) 

После загрузки данных меню настроек будет выглядить так:
![Screenshot](../images/MQB/tires.jpg) 
    
!!! warning
    После записи машина на некоторое время станет новогодней ёлкой - будут ошибки и отказы по всем блокам.   
    Беспокоиться не надо - в течение 10 минут все само починится.
    
### Косвенный контроль давления в шинах

![Screenshot](../images/MQB/analog_tires.png) 

Активация в блоке ABS
```
Блок 03 → Кодирование
> Байт 27 → включаем биты 4,5 (1-й вариант) или биты 4,5,6 (2-й вариант - для парк-пилота) 
> Байт 28 → включаем бит 7
→ Применить (с перезагрузкой блока)
```

Активация отображения на приборной панели
```
Блок 17 → Кодирование  
> Байт 4 → включаем бит 0 - Indirect Tire Pressure Monitoring System(TPMS) installed (Индикатор контроля давления в шинах)
→ Применить (с перезагрузкой блока)
```

Активация в меню магнитолы
```
Блок 5F → Адаптация
> Car_Function_Adaptations_Gen2
>> menu_display_rdk → activate
>> menu_display_rdk_over_threshold_high → activate
→ Применить 

> Car_Function_List_BAP_Gen2
>> tire_pressure_system_0x07 → activate
>> tire_pressure_system_0x07_msg_bus → CAN_Comfort (возможно Suspension_data_bus)
→ Применить 
```

!!! note ""
    После кодирования необходимо включить зажигание, магнитолу и на экране контроля давления нажать виртуальную клавишу SET