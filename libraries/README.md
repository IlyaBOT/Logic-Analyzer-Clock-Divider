# Проектные библиотеки R4

Стандартные символы, footprint и STEP взяты из установленного KiCad10.0.6. Источники: [symbols](https://gitlab.com/kicad/libraries/kicad-symbols), [footprints](https://gitlab.com/kicad/libraries/kicad-footprints), [packages3D](https://gitlab.com/kicad/libraries/kicad-packages3D). Лицензия [CC-BY-SA4.0 с исключением KiCad](https://www.kicad.org/libraries/license/), текст/исключение в LICENSE.md.

U1 на базе графики74LS161 с именами выводов поTI CD74ACT161; наследование раскрыто. U3 стандартныйTLV75533PDBV. J4 стандартный Conn_01x02 и PinHeader_1x02_P2.54mm_Vertical со STEP, pin1 +5V/pin2 GND. USB shield pin переименован SH по стандартному footprint. У стандартных footprint убран повторяющий Reference user-text наFab; геометрия не менялась. U1 имеет socket+стандартныйDIP с Z3.5mm, genericLED STEP перекрашен жёлтым. Точные закупочные корпуса этим не подтверждены.

J2_Edge_2x05 и J3_Edge_2x05 собственные UNVERIFIED footprints: SMD обе поверхности, без отверстий/paste, зеркальная геометрияX без перестановки строк. У них нет утверждённых механических3D-моделей. Проверка 2D не доказывает физическую посадку.

Все используемые библиотеки и модели локальные `${KIPRJMOD}`. Проверен перенос в другую папку на том же компьютере; другойПК не испытывался.
