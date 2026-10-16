"""R4 handoff from completed native checks; do not fabricate unknown connectors."""
from pathlib import Path
import json,csv
ROOT=Path(__file__).resolve().parents[1]; NAME='ACT161_Frequency_Divider'
def write(path,text):(ROOT/path).write_text(text.strip()+'\n',encoding='utf-8')
if __name__=='__main__':
    runs=json.loads((ROOT/'reports'/'native_runs.json').read_text())
    assert all(r['exit_code']==0 for r in runs),'Native checks must pass before handoff'
    comp=json.loads((ROOT/'reports'/'components.json').read_text())
    metrics=json.loads((ROOT/'reports'/'routing_metrics.json').read_text())
    f=metrics['tracks_length_mm']['F.Cu'];b=metrics['tracks_length_mm']['B.Cu']
    variants={'default_5V':{'U1':'CD74ACT161E','fit':['R5'],'dnp':['R6','U3','C4'],'VCC_LOGIC_V':5,'power_input':{'J1':'USB 5V','J4':{'1':'+5V','2':'GND'},'one_source_only':True},'datasheet_max_clock_MHz_full_temperature':80},'optional_3V3':{'U1':'CD74AC161E','fit':['R6','U3','C4'],'dnp':['R5'],'VCC_LOGIC_V':3.3,'power_input':{'J1':'USB 5V','J4':{'1':'+5V','2':'GND'},'one_source_only':True},'datasheet_max_clock_MHz_full_temperature':64}}
    (ROOT/'reports'/'assembly_variants.json').write_text(json.dumps(variants,indent=2),encoding='utf-8')
    requirements={
      'U1':'TI CD74ACT161E, PDIP-16 in SCS-16 socket; DEFAULT 5V. Optional 3.3V requires replacement by CD74AC161E.',
      'U3':'OPTIONAL 3.3V ONLY: TI TLV75533PDBVR SOT-23-5. Fit with R6/C4; remove R5 and replace U1 by CD74AC161E.',
      'J1':'Exact Molex 47346-0001; substitutions require a matching footprint.',
      'J2':'CONNFLY DS1002-01-2x5V13-JK, modified edge mounting, UNVERIFIED: measure tails/body/mating number order before manufacture.',
      'J3':'Male 2x5, 2.54mm, modified edge mounting. No approved MPN or mechanical drawing: UNVERIFIED. Not a bottom THT header.',
      'J4':'Male THT header 1x2, 2.54mm pitch, 1.0mm holes, vertical. Pin1 +5V, pin2 GND. Regulated 5V alternative input; use either USB or J4, never both simultaneously.',
      'C1':'100nF 25V X7R 0603, +/-20%; directly next to U1 pin 16.',
      'C2':'4.7uF 16V X7R 0805, +/-20%; effective >=1uF at bias/temperature for optional U3 input.',
      'C4':'OPTIONAL 3.3V ONLY: 4.7uF 16V X7R 0805; effective >=1uF at bias/temperature for U3 output.',
      'C5':'1uF 16V X7R 0805, +/-20%; bulk on selected VCC_LOGIC.',
      'LED1':'Yellow 3mm THT, 2.54mm lead pitch; pad1 cathode, pad2 anode. Verify purchased part.',
      'R13':'R_LED: 5.1k 0603 1% >=0.1W; LED indicates common input 5V from USB or J4, not selected U1 supply.',
      'R14':'R_CLK: fit 0R 0603; 0-100R option only after observing waveform at U1 pin2.',
      'R15':'R_PD: 10k 0603 1% >=0.1W; pull-down, 0.5mA at 5V.',
      'R5':'0R 0603 DEFAULT 5V supply link; mutually exclusive with R6.',
      'R6':'0R 0603 OPTIONAL 3.3V supply link; remove R5 first; requires U3/C4 and CD74AC161E in socket.'}
    with (ROOT/'reports'/'BOM.csv').open('w',encoding='utf-8-sig',newline='') as stream:
      w=csv.writer(stream);w.writerow(['Reference','Quantity','Value_or_MPN','Footprint','Default_assembly','Requirements'])
      for ref,c in comp.items():
        if ref.startswith('H'):continue
        detail=requirements.get(ref,'47R 0603 1% >=0.1W; initial series damping; tune for actual cable/input capacitance.')
        w.writerow([ref,1,c['value'],c['fp'],'DNP' if c['dnp'] else 'FIT',detail])
      w.writerow(['U1 ALT',1,'CD74AC161E','Same DIP-16 socket','OPTIONAL REPLACEMENT','Replace U1 for 3.3V operation; no second PCB IC. Clock 0..VCC, max64MHz -55..125C; original ACT cannot run at 3.3V.'])
      w.writerow(['U1 socket',1,'SCS-16','DIP-16_W7.62mm_Socket','FIT','Separate socket in U1 holes; 7.62mm rows, 2.54mm pitch; verify exact body.'])
      w.writerow(['H1-H4',4,'M3 mounting hardware','NPTH 3.2mm','MECHANICAL','Envelope <=6.4mm; check standoffs/enclosure.'])
    write('README.md',r'''
# ACT161 Frequency Divider - R4

Основная редактируемая ревизия R4, KiCad 10.0.6, обновлена 2026-10-09. Прежняя папка R3 удалена. Взята ваша ручная разводка R4: все её дорожки/via, положения компонентов и контур сохранены. Текущий размер платы 42.8x27.6x1.6mm; два слоя, DIP-16/SCS-16 и четыре отверстия M3.

**До изготовления: оба торцевых разъёма UNVERIFIED, реальная распиновка/уровни анализатора неизвестны. Аппаратных измерений на 80MHz нет.**

Открыть `ACT161_Frequency_Divider.kicad_pro` в KiCad 10 или совместимой новой версии. Переносить всю папку: символы, footprint и модели локальные, пути `${KIPRJMOD}`. Схема и PCB нативные; генераторы не нужны для ручного редактирования.

## Изменения R4

J2 расположен на левой кромке, J3 - на правой. У каждого пять SMD-площадок F.Cu и пять B.Cu, без отверстий и без пасты. J3 больше не является нижним THT-разъёмом. Нечётные контакты обоих разъёмов на F.Cu, чётные на B.Cu; строки 1/2 сверху. Механические модели этих разъёмов отсутствуют: выполнена 2D-проверка, посадка реальных деталей не подтверждена.

SN74LVC125APW, C3 и выходные селекторные резисторы удалены. R1-R4=47R соединяют QA/QB/QC/QD напрямую с DIV2/4/8/16. По умолчанию U1 CD74ACT161E получает 5V через R5=0R; R6, U3, C4 не устанавливаются. LED питается от общей входной шины 5V (USB или J4). Пять PASS проходят напрямую между одинаковыми номерами J2/J3. USB +5V не соединено с контактами J2/J3.

## Питание проводами через J4

Между Micro-USB J1 и LED1 установлена вертикальная штыревая гребёнка J4 1x2, шаг 2.54mm, отверстия 1mm. При виде сверху, USB наверху: верхний квадратный контакт 1 = +5V, нижний круглый контакт 2 = GND. Полярность подписана на плате. Гребёнка включена в BOM и в схему, footprint и STEP локальные.

Подать стабилизированные 5V и общий GND от основной схемы. USB и J4 соединены с одной шиной напрямую: использовать только один источник за раз. При питании через J4 отключить USB-кабель, иначе питание может попасть в USB-порт. В опциональной сборке с выходами 3.3V на J4 по-прежнему подаются 5V; это вход до U3. LED работает от любого из этих двух входов.

В исходной R4 дополнены пять незавершённых соединений у J2/J3, исправлены пересечения/размер надписей и расстояние между QR и ссылкой. Исходные нативные файлы сохранены в `reports/user_R4_original.zip`; сравнение геометрии - `input_user_layout.json` и тест сохранения пользовательской разводки.

## Опция 3.3V без выходного буфера

Это отдельный вариант сборки с заменой U1, а не переключение напряжения установленного ACT161. При выключенном питании удалить R5, заменить CD74ACT161E в панельке на совместимый по выводам CD74AC161E, установить U3 TLV75533PDBVR, C4 и R6=0R. Все управляющие входы и развязка U1 питаются от выбранного VCC_LOGIC. Одновременно R5/R6 не устанавливать: это соединит 5V с выходом 3.3V стабилизатора.

CD74ACT161E требует 4.5-5.5V и не допускается в сборке 3.3V. Для CD74AC161E при 3.3V datasheet гарантирует до 64MHz (-55..125C), 73MHz (-40..85C), а не 80MHz. CLK должен быть 0..VCC и с полными CMOS-уровнями; 5V CLK напрямую запрещён в режиме 3.3V. Если 3.3V выходы нужны при 80MHz с сохранением ACT161, потребуется внешний преобразователь уровней либо отдельная переработка схемы. Источники и временные параметры в `reports/validation.md`.

## Проверки и файлы

Сохранённые ERC/DRC, 15 успешных тестов и `final_audit.txt` в `reports/` относятся к снимку из `checked_sha256.json`. Текущие PCB и `.kicad_pro` отличаются от этого снимка. Повторная проверка 2026-10-17: ERC без нарушений; DRC без ошибок, с одним предупреждением о несовпадении J4 с библиотечным footprint; тесты 13/15, два расхождения с прежней компоновкой. Подробности и список файлов для очистки — `reports/repository_audit.md`. Прежняя проверка переноса выполнялась в другой папке на этом же ПК, не на другой машине.

`docs/` содержит PDF схемы, двух copper и двух assembly видов, а также `pinout.md`. `previews/` содержит PNG, SVG каждого слоя и два настоящих 3D-рендера KiCad. BOM и варианты сборки в `reports/BOM.csv` и `assembly_variants.json`.

Чертежи и изображения относятся к исходникам, записанным в `reports/export_manifest.json`; после изменений PCB их нужно обновить. `.gitignore` исключает автокопии и локальные настройки KiCad, файлы Freerouting, кэши Python, старые генераторы и их логи. Нативные файлы, локальные библиотеки, документация, актуальные отчёты и `reports/user_R4_original.zip` остаются доступными для Git.

`scripts/check_native.py` запускает ERC/DRC/tests в этой установке KiCad. Старые генераторы `design.py` и `build_pcb.py` заблокированы от запуска, чтобы не перезаписать вашу ручную разводку. Нативные KiCad-файлы - основной источник проекта. `export.py` обновляет чертежи, `document.py` документацию. В скриптах заданы пути к установленным здесь KiCad/Poppler.

Перед подключением проверить pinout и допустимые уровни анализатора, посадку обоих торцевых разъёмов, точную панельку и приобретённые MLCC/LED. Подавать CLK после стабилизации питания; измерять питание и CLK у U1.2, начинать с низкой частоты. Выходы рассчитаны на высокоомные входы, не на DC-нагрузку 50ohm. В фазе включения счётчика нет определённого сброса. Прямой счёт 433MHz не предусмотрен. Gerber/Drill не выпускались, изготовление не заказывалось.
''')
    write('docs/pinout.md',r'''
# Контакты, стороны и варианты R4

**До проверки документации/прозвонки конкретного анализатора J2 не подключать. Default выходы теперь 5V; 5V tolerance анализатора неизвестна.**

| Номер | J2 слева, анализатор | J3 справа, DUT |
|---|---|---|
| 1 | DIV2 | CLK_IN |
| 2 | PASS2 | PASS2 |
| 3 | DIV4 | NC |
| 4 | PASS4 | PASS4 |
| 5 | DIV8 | NC |
| 6 | PASS6 | PASS6 |
| 7 | DIV16 | NC |
| 8 | PASS8 | PASS8 |
| 9 | GND | GND |
| 10 | PASS10 | PASS10 |

PASS2/4/6/8/10 имеют только два узла J2.N/J3.N, без связи с USB-питанием, GND или счётчиком. Если контакт PASS анализатора является питанием, он напрямую попадёт на соответствующий контакт DUT: проверить возможный конфликт источников.

## Вид сверху, USB наверху

Плата 42.8x27.6mm. Координаты далее относительно верхнего левого угла: J2 - левая кромка X=0, J3 - правая X=42.8. В нативном PCB этот угол имеет координаты (126.6,84.4)mm. Оба разъёма припаяны к поверхности сверху/снизу, без отверстий. Начало координат слева сверху, Y направлен вниз.

| Строка Y, mm | J2 F.Cu | J2 B.Cu | J3 F.Cu | J3 B.Cu |
|---|---|---|---|---|
| 8.92 | 1 | 2 | 1 | 2 |
| 11.46 | 3 | 4 | 3 | 4 |
| 14.00 | 5 | 6 | 5 | 6 |
| 16.54 | 7 | 8 | 7 | 8 |
| 19.08 | 9 | 10 | 9 | 10 |

Центры J2 X=2.10, J3 X=40.70 (абсолютно 128.7 и 167.3mm). Площадки 3.20x1.60mm, шаг строк 2.54mm, край меди в 0.50mm от Edge.Cuts. Ни F.Paste, ни B.Paste нет; ручная пайка открытых площадок. J3 footprint является горизонтальным зеркалом геометрии J2 без изменения строк/номеров. Простое вращение J2 на 180 градусов поменяло бы верх/низ строк, поэтому для J3 сделан отдельный footprint.

Для вида снизу повернуть плату вокруг вертикальной оси, сохраняя USB сверху: J3 окажется слева, J2 справа, на обеих видимых поверхностях сверху вниз 2/4/6/8/10. PDF back отражён для этого вида. Эти номера относятся к площадкам PCB; порядок номеров на mating-стороне реальных разъёмов требует измерения.

U1: pin1 квадратный, вырез панельки направлен к J3. LED pin1=K, pin2=A. USB: 1 VBUS, 2 D-, 3 D+, 4 ID, 5 GND, SH экран (все SH на GND). R13=5.1k - R_LED, R14=0R - R_CLK, R15=10k - R_PD.

## J4 - альтернативный вход питания

| Контакт | Сеть | Положение при виде сверху, USB наверху |
|---|---|---|
| 1, квадратный | +5V | Верхний, X=28.40 / Y=1.80mm |
| 2, круглый | GND | Нижний, X=28.40 / Y=4.34mm |

Гребёнка 1x2, шаг 2.54mm, THT отверстия 1mm, находится между USB и LED. В нативном PCB центр pin1 (155.0,86.2)mm. Подавать стабилизированные 5V и GND. J4 напрямую связан с USB VBUS: подключать USB или J4 по отдельности, одновременно не питать. В опции 3.3V вход J4 остаётся 5V, напряжение U1 снижает U3. LED показывает наличие общей шины +5V от любого входа.

## Напряжение

| Сборка | U1 в панельке | Установить | Не устанавливать | Выходы |
|---|---|---|---|---|
| Default | CD74ACT161E | R5 | R6/U3/C4 | около 5V |
| Optional | CD74AC161E | R6/U3/C4 | R5 | около 3.3V |

Во втором варианте C4 эффективный >=1uF, U3 TLV75533PDBVR. Все изменения при отключённых USB и J4. R5 и R6 вместе запрещены; ACT161 при 3.3V запрещён. Предел второго варианта 64MHz во всём диапазоне температуры и CLK 0..VCC. Это вариант сборки с заменой IC, не рабочий переключатель напряжения. Совместимость с входами анализатора проверить в обоих случаях.

## Механика: оба UNVERIFIED

[CONNFLY DS1002](https://www.connfly.com/static/upload/file/pdf/DS1002-01.pdf) не подтверждает монтаж выбранного J2 на кромку. Для J3 не предоставлен MPN или чертёж male-разъёма такого монтажа. У обычных двухрядных разъёмов расстояние рядов 2.54mm, поверхности PCB находятся на расстоянии 1.6mm. Нужны замеры и при необходимости формовка выводов/фиксация корпуса. Проверить доступ к пайке, mating-нумерацию и удержание разъёмов. Если переделка штатных контактов непригодна, нужны предназначенные для торцевого монтажа разъёмы/переходники и повторная CAD-проверка. До этого статус изготовления HOLD.
''')
    write('reports/validation.md',f'''
# Проверка R4 - 2026-10-09

Это исторический отчёт для снимка `checked_sha256.json`. Текущие PCB и настройки проекта отличаются; результаты повторной проверки от 2026-10-17 находятся в [repository_audit.md](repository_audit.md).

Windows, установленный KiCad 10.0.6 и bundled pcbnew/Python. Ручная R4 сделана основной, прежняя папка R3 удалена. Добавлен J4 и завершены пять соединений у торцевых разъёмов. Все 108 исходных дорожек/via, позиции всех 23 исходных компонентов и контур сохранены (отдельный тест по UUID и геометрии). Исходные native-файлы архивированы в user_R4_original.zip; входной DRC с 14 нарушениями и 5 unconnected сохранён как input_user_DRC.txt. Это CAD-проверка; собранное устройство не испытано.

## Результаты

| Проверка | Фактический результат |
|---|---|
| ERC `--severity-all --exit-code-violations` | 0 ошибок, 0 предупреждений; exit0 |
| DRC `--schematic-parity --all-track-errors --severity-all --refill-zones` | 0 ошибок, 0 предупреждений; exit0 |
| Несоединённые pads / schematic parity | 0 / 0 |
| Netlist и физические pad nets | Все контакты сверены с ожидаемыми сетями |
| U1/U3 pin maps | Сверены с официальными TI datasheet |
| PASS / USB или J4 power | Прямые пары одинаковых номеров, питания на J2/J3 нет |
| Разъёмы | Оба edge SMD: odd F.Cu / even B.Cu, никаких отверстий/paste |
| Счёт/деление/управление | 4 логических теста, 4096 сценариев управления, 256 тактов, все начальные фазы |
| Общий testbench | 15/15 успешно, включая J4 и сохранение разводки, `tests.txt` |
| PDF/SVG/3D | Нативный экспорт KiCad, PNG Poppler, визуальная проверка обеих сторон |
| Финальный аудит | `final_audit.txt`: hash, комплект, courtyard, via centers, mask, локальные модели |
| Перенос | Другая папка на этом же ПК; ERC/DRC/parity0, `portable_runs.json` |

Команды и настоящие коды возврата в `native_runs.json`, SHA256 нативных файлов в `checked_sha256.json`. Исключения DRC пусты; пользовательские настройки сохранены, критические проверки имеют уровень error. Стандартная таблица rule_severities, записанная GUI KiCad, сохранена. Минимумы: clearance0.20, silk0.15, width0.20, via0.60, edge0.50mm; фактические via0.65/drill0.30mm. Минимумы проверены в сохранённом проекте. Стандартные Ignored checks KiCad: отсутствующий courtyard, via centering, tuning geometry, symbol filters, footprint types. Все footprint имеют courtyard, pad types/номера и центры сигнал-via проверены отдельным аудитом. Исключённых нарушений нет.

## Почему удалён SN74LVC125APW

В R3 он преобразовывал 5V счётчика в 3.3V, что было выбрано как default. По новым требованиям default5V, поэтому U2, C3 и 8 выходных связок удалены. QA..QD теперь через R1..R4=47R подключены к J2. Установленная default схема содержит один активный логический IC U1. U3/C4/R6 - места под опцию, в default DNP. Схема содержит PWR_FLAG на VCC_LOGIC: ERC не проводит питание сквозь пассивную перемычку R5.

## Проверка электрических режимов

[TI CD74ACT161, SCHS298B](https://www.ti.com/lit/ds/symlink/cd74act161.pdf): питание4.5-5.5V, TTL CLK VIH>=2V/VIL<=0.8V, вход0..VCC. Pin1=/CLR,2=CLK,3..6=A..D,7=ENP,8=GND,9=/LOAD,10=ENT,11..14=QD/QC/QB/QA,15=RCO,16=VCC. /CLR,/LOAD,ENP,ENT и VCC связаны с VCC_LOGIC; A..D к GND, RCO NC. CLK положительный фронт. При запуске без clear фаза неизвестна. Default R5 соединяет общую шину входа USB/J4 +5V с VCC_LOGIC.

Для ACT полный температурный диапазон -55..125C: fclock80MHz, CLK high/low>=6.2ns, clear low>=6ns, setup data5ns/load6ns, recovery6ns, hold data/ENP/ENT0ns; tpd CLK-Q<=16.5ns при CL50pF. Для 80MHz T12.5ns, duty49.6-50.4%; при 50% запас на каждом полупериоде всего0.05ns. Реальный источник/фронты/нагрузка и питание требуют осциллографа. Подача сигнала при отключённом U1 может питать его через защитные диоды.

[TI CD74AC161, SCHS239D от 2024-05](https://www.ti.com/lit/gpn/CD74AC161): PDIP E и pinout совпадают с ACT, питание1.5-5.5V. При 3.3V+/-0.3V и CL50pF fmax64MHz (-55..125C),73MHz (-40..85C); CLK high/low>=7.7ns для полного диапазона, clear low>=7ns. Именно CD74AC161E является заменой U1 для опции3.3V. CLK должен оставаться в0..VCC с полными CMOS-уровнями, 5V CLK напрямую недопустим. Предел80MHz для этого режима не гарантирован. Не подавать3.3V на CD74ACT161E.

[TI TLV755P](https://www.ti.com/lit/ds/symlink/tlv755p.pdf): U3 SOT23-5 IN1=+5V, GND2, EN3=+5V, NC4,OUT5=+3V3. C2/C4 должны иметь эффективные>=1uF при bias/температуре. Для опции удалитьR5, установитьU3/C4/R6, заменитьU1. R5/R6 вместе закоротят разные источники: запрещено. Данные о вариантах сборки в `assembly_variants.json`; PCB и схема отражают default сборку.

[USB Molex SD-47346-001](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/473/47346/473460001_sd.pdf): стандартный footprint/model KiCad47346-0001. D-/D+/ID NC, все SH наGND. USB5V не выведено на J2/J3. Default входная ёмкость около5.8uF (C2+C5+C1); оценка, не USB сертификация. LED cathode1 кGND, anode2 черезR13=5.1k к общей шине USB/J4 +5V: около0.59mA приVf2V. Светодиод подтверждает наличие входных 5V от USB или J4, а не VCC_LOGIC.

R14 default0R; опция100R при Cin U1до10pF даёт tau1ns только по IC, поэтому требует измерения на80MHz. R15=10k удерживает CLK без источника, статический ток0.5mA при5V. R1..R4=47R начальные демпфирующие значения: tau0.47ns при10pF,2.35ns при50pF без сопротивления драйвера. Высокоомный анализатор, согласование/нагрузка/звон не проверены аппаратно. Резисторы расположены по пути к J2; контролируемое волновое сопротивление/идеальное согласование источника не заявляются. Буферных DNP-ответвлений R3 больше нет.

## Плата

42.8x27.6x1.6mm, площадь1181.28mm2. Контур пользовательской R4 сохранён. Два слоя; B.Cu{b:.1f}mm ({100*b/(b+f):.1f}% длины),F.Cu{f:.1f}mm. Via всего{metrics['vias']},GND{metrics['ground_vias']},остальные{metrics['signal_vias']}. Всех необходимых соединений трассировка завершена. GND заливка на обеих сторонах с удалением всех изолированных островков и stitching-via возле развязки/CLK и между участками. Обратный путь B.Cu преимущественно F.Cu; количественная SI/EMI-проверка не проведена.

Минимальная дорожка0.20mm/clearance0.20mm; подключение J4 +5V дорожкой0.40mm, copper edge0.50mm, via0.65/0.30mm. При35um меди 30mm трассы0.20mm дают около0.075ohm (3.75mV при50mA). Расчётный ток U1 по типичному Cpd66pF при80MHz/5V около26.4mA без внешней нагрузки. Это расчёты, не измерения. Маска expansion0.05mm/minimum web0.10mm. C1 рядом с U1.16; четыре NPTH3.2mm с envelope6.4mm свободны от courtyard компонентов, трассы обходят монтажные зоны.

## Визуальная проверка и механика

PDF схемы, copper обеих сторон и assembly экспортированы KiCad, затем Poppler PNG. Отдельные SVG F.Cu/B.Cu/F.Silkscreen/B.Silkscreen/Edge.Cuts в `previews/layers`. 3D-рендеры нативные KiCad: DIP и socket, USB, жёлтый LED, новый штыревой J4 1x2, DNP скрыты. Socket подъём IC3.5mm - номинальная модель, точная SCS-16 не подтверждена. LED модель generic, не закупочный MPN. Интерактивный GUI и физическая сборка не использовались как доказательства.

У обоих разъёмов 5F+5B площадок, no holes/paste. Относительно верхнего левого угла J2 X2.1,J3 X40.7; Y8.92+2.54i, pad3.2x1.6mm, copper setback0.5mm. Fodd/Beven у обоих, строки не перевёрнуты. Mating-номера конкретных деталей неизвестны. Для J2 [CONNFLY чертёж](https://www.connfly.com/static/upload/file/pdf/DS1002-01.pdf) не подтверждает торцевой монтаж V/T. У J3 нет предоставленного maleMPN. Предварительная толщина1.6mm не совпадает с межрядным шагом2.54mm: нужны измерения/формовка и фиксация. У обоих нет утверждённых 3D-моделей, проверка площадок только2D.

## Открытые ограничения

1. Оба разъёма UNVERIFIED: подтвердить детали, посадку, толщину, пайку и mating-нумерацию. При несовместимости нужен специальный edge connector либо переходник и новый CAD-check.
2. Анализатор неизвестен: проверить реальные номера,GND,PASS и допустимые напряжения. Default5V не является заявлением о его 5V tolerance.
3. Опция3.3V требует заменыU1 и ограничения частоты/CLK, а не простой перестановки одной перемычки. Нет гарантии80MHz для AC3.3V; ACT3.3V запрещён.
4. Точная SCS-16/LED и MLCC effectiveC требуют проверки закупочных MPN. CAD-модели их не подтверждают.
5. Логическая симуляция4096 сценариев/256 тактов не моделирует задержки/фронты и не доказывает физические80MHz. Нужны реальные измерения питания, счёта, CLK, звона, нагрузки и нагрева. 433MHz напрямую не поддерживается.
6. Другой ПК не проверен. Gerber/Drill не выпускались, плата не заказывалась. Статус производства HOLD.
''')
    write('libraries/README.md',r'''
# Проектные библиотеки R4

Стандартные символы, footprint и STEP взяты из установленного KiCad10.0.6. Источники: [symbols](https://gitlab.com/kicad/libraries/kicad-symbols), [footprints](https://gitlab.com/kicad/libraries/kicad-footprints), [packages3D](https://gitlab.com/kicad/libraries/kicad-packages3D). Лицензия [CC-BY-SA4.0 с исключением KiCad](https://www.kicad.org/libraries/license/), текст/исключение в LICENSE.md.

U1 на базе графики74LS161 с именами выводов поTI CD74ACT161; наследование раскрыто. U3 стандартныйTLV75533PDBV. J4 стандартный Conn_01x02 и PinHeader_1x02_P2.54mm_Vertical со STEP, pin1 +5V/pin2 GND. USB shield pin переименован SH по стандартному footprint. У стандартных footprint убран повторяющий Reference user-text наFab; геометрия не менялась. U1 имеет socket+стандартныйDIP с Z3.5mm, genericLED STEP перекрашен жёлтым. Точные закупочные корпуса этим не подтверждены.

J2_Edge_2x05 и J3_Edge_2x05 собственные UNVERIFIED footprints: SMD обе поверхности, без отверстий/paste, зеркальная геометрияX без перестановки строк. У них нет утверждённых механических3D-моделей. Проверка 2D не доказывает физическую посадку.

Все используемые библиотеки и модели локальные `${KIPRJMOD}`. Проверен перенос в другую папку на том же компьютере; другойПК не испытывался.
''')
    print('R4 BOM, pinout, variants, README and validation written.')
