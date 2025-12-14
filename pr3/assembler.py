import sys
import json
import struct # Для упаковки целых чисел в байты
from typing import List, Dict, Any

# Определение опкодов (условно для примера)
OPCODES = {
    'load_const': 0x01,
    'read': 0x02,
    'write': 0x03,
    'bswap': 0x04,
    # ... другие команды ...
}

def parse_asm_line(line: str) -> Dict[str, Any]:
    """Парсит одну строку, содержащую JSON-объект команды."""
    try:
        command_dict = json.loads(line.strip())
        return command_dict
    except json.JSONDecodeError as e:
        raise ValueError(f"Ошибка парсинга JSON: {e}")

def translate_ir_to_machine_code(ir_list: List[Dict[str, Any]], output_file_path: str):
    """
    Преобразует список команд IR в машинный код и записывает в бинарный файл.
    """
    binary_data = bytearray()
    for ir_cmd in ir_list:
        opcode_name = ir_cmd.get('cmd')
        args = ir_cmd.get('args', {})

        if opcode_name not in OPCODES:
            raise ValueError(f"Неизвестная команда '{opcode_name}' в IR.")

        opcode = OPCODES[opcode_name]

        # --- Трансляция в байты (гипотетический формат) ---
        # load_const dst value
        if opcode_name == 'load_const':
            dst_reg = args.get('dst', 0)
            value = args.get('value', 0)
            # Упаковываем: opcode (1B), padding (4b), dst_reg (28b), value (32b)
            # Используем little-endian ('<'), как часто делается.
            # Для dst_reg: маска 0xFFFFFFF (28 бит), для value: 0xFFFFFFFF (32 бита)
            # Упаковываем как 2 x 32-bit целых: [opcode + dst_part, value]
            # opcode (8b) идет в младшие 8 бит первого слова
            # dst_reg (28b) идет в старшие 28 бит первого слова
            first_word = (dst_reg & 0xFFFFFFF) << 4 | (opcode & 0xFF)
            second_word = value & 0xFFFFFFFF
            binary_data.extend(struct.pack('<II', first_word, second_word))

        # read dst src_addr
        elif opcode_name == 'read':
            dst_reg = args.get('dst', 0)
            src_addr = args.get('src', 0)
            first_word = (dst_reg & 0xFFFFFFF) << 4 | (opcode & 0xFF)
            second_word = src_addr & 0xFFFFFFFF
            binary_data.extend(struct.pack('<II', first_word, second_word))

        # write addr src
        elif opcode_name == 'write':
            addr = args.get('addr', 0)
            src_reg = args.get('src', 0)
            # addr (32b) в первом слове, src_reg (28b) в старших 28 битах второго слова
            first_word = addr & 0xFFFFFFFF
            second_word = (src_reg & 0xFFFFFFF) << 4 | (opcode & 0xFF)
            binary_data.extend(struct.pack('<II', first_word, second_word))

        # bswap reg
        elif opcode_name == 'bswap':
            reg = args.get('dst', 0) # используем 'dst' для consistency с load_const
            first_word = (reg & 0xFFFFFFF) << 4 | (opcode & 0xFF)
            # Второе слово - резерв (нули)
            second_word = 0
            binary_data.extend(struct.pack('<II', first_word, second_word))

        else:
            raise ValueError(f"Команда '{opcode_name}' пока не реализована для трансляции в машинный код.")

    # --- Запись в бинарный файл ---
    try:
        with open(output_file_path, 'wb') as bin_f:
            bin_f.write(binary_data)
    except Exception as e:
        raise IOError(f"Ошибка при записи бинарного файла: {e}")

def display_binary_file(file_path: str):
    """
    Считывает бинарный файл и выводит его содержимое в шестнадцатеричном виде.
    """
    try:
        with open(file_path, 'rb') as bin_f:
            data = bin_f.read()
        if data:
            hex_str = " ".join([f"0x{byte:02X}" for byte in data])
            print(hex_str)
        else:
            print("(Файл пуст)")
    except FileNotFoundError:
        print(f"Ошибка: Бинарный файл {file_path} не найден для отображения.")
    except Exception as e:
        print(f"Ошибка при чтении бинарного файла для отображения: {e}")

def assemble(input_file_path: str, output_file_path: str, test_mode: bool):
    """
    Основная функция ассемблера.
    Читает .asm файл, строит промежуточное представление (IR),
    транслирует IR в машинный код и записывает в .bin файл.
    """
    ir_list: List[Dict[str, Any]] = []

    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                stripped_line = line.strip()
                if not stripped_line or stripped_line.startswith('#'):
                    continue

                try:
                    ir_cmd = parse_asm_line(stripped_line)
                    if 'cmd' not in ir_cmd:
                        print(f"Предупреждение (строка {line_num}): "
                              f"'cmd' отсутствует в {ir_cmd}. Команда пропущена.")
                        continue
                    ir_list.append(ir_cmd)
                except ValueError as e:
                    print(f"Ошибка (строка {line_num}): {e}")
                    return

    except FileNotFoundError:
        print(f"Ошибка: Файл {input_file_path} не найден.")
        return
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return

    # --- Вызов функции трансляции (Этап 2) ---
    try:
        translate_ir_to_machine_code(ir_list, output_file_path)
        print(f"Ассемблировано команд: {len(ir_list)}")
    except (ValueError, IOError) as e:
        print(f"Ошибка трансляции в машинный код: {e}")
        return # Прекращаем работу при ошибке трансляции

    # --- Режим тестирования ---
    if test_mode:
        print("--- Начало байтового вывода (режим тестирования) ---")
        display_binary_file(output_file_path)
        print("--- Конец байтового вывода ---")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python assembler.py <input.asm> <output.bin> [--test]")
        sys.exit(1)

    input_asm_file = sys.argv[1]
    output_bin_file = sys.argv[2]
    test_flag_present = '--test' in sys.argv

    assemble(input_asm_file, output_bin_file, test_flag_present)
