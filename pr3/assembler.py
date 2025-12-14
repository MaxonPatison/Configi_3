import sys
import json
from typing import List, Dict, Any


def parse_asm_line(line: str) -> Dict[str, Any]:
    """
    Парсит одну строку, содержащую JSON-объект команды.
    Выбрасывает ValueError при ошибке.
    """
    try:
        command_dict = json.loads(line.strip())
        return command_dict
    except json.JSONDecodeError as e:
        raise ValueError(f"Ошибка парсинга JSON: {e}")


def assemble(input_file_path: str, output_file_path: str, test_mode: bool):
    """
    Основная функция ассемблера.
    Читает .asm файл, строит промежуточное представление (IR).
    """
    ir_list: List[Dict[str, Any]] = []  # Список для промежуточного представления

    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                stripped_line = line.strip()

                # Пропускаем пустые строки и комментарии
                if not stripped_line or stripped_line.startswith('#'):
                    continue

                try:
                    ir_cmd = parse_asm_line(stripped_line)

                    # Проверяем, что у команды есть ключ 'cmd'
                    if 'cmd' not in ir_cmd:
                        print(f"Предупреждение (строка {line_num}): "
                              f"'cmd' отсутствует в {ir_cmd}. Команда пропущена.")
                        continue

                    ir_list.append(ir_cmd)

                except ValueError as e:
                    # Ошибка при парсинге конкретной строки
                    print(f"Ошибка (строка {line_num}): {e}")
                    return  # Прекращаем работу при первой ошибке

    except FileNotFoundError:
        print(f"Ошибка: Файл {input_file_path} не найден.")
        return
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return

    # Вывод промежуточного представления в режиме тестирования
    if test_mode:
        print("--- Начало промежуточного представления (IR) ---")
        for index, command in enumerate(ir_list):
            print(f"{index}: {command}")
        print("--- Конец промежуточного представления ---")

    print(f"Ассемблирование завершено. Промежуточное представление содержит {len(ir_list)} команд.")


if __name__ == "__main__":
    # Проверка количества аргументов
    if len(sys.argv) < 3:
        print("Usage: python assembler.py <input.asm> <output.bin> [--test]")
        sys.exit(1)

    # Получение аргументов
    input_asm_file = sys.argv[1]
    output_bin_file = sys.argv[2]
    test_flag_present = '--test' in sys.argv

    # Вызов основной функции
    assemble(input_asm_file, output_bin_file, test_flag_present)
