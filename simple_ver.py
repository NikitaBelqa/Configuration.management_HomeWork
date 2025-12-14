#!/usr/bin/env python3
"""
Упрощённый конвертер учебного конфигурационного языка в XML
Вариант №6
"""

import sys
import argparse
import math
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

# ==================== ПАРСЕР ====================

def remove_comments(text):
    """Удаляет многострочные комментарии --[[ ... ]]"""
    return re.sub(r'--\[\[.*?\]\]', '', text, flags=re.DOTALL)

def parse_hex_number(token):
    """Парсит шестнадцатеричное число 0x..."""
    if token.startswith('0x'):
        try:
            return int(token, 16)
        except ValueError:
            raise ValueError(f"Неверное шестнадцатеричное число: {token}")
    return None

def tokenize(text):
    """Разбивает текст на токены"""
    text = remove_comments(text)
    
    # Регулярное выражение для токенов
    token_pattern = re.compile(r'''
        begin|end|          # ключевые слова
        :=|;|               # операторы
        \^\(|\)|            # константные выражения
        sqrt|\+             # операции
        |0x[0-9a-fA-F]+     # шестнадцатеричные числа
        |[a-z]+             # имена
        |\S                 # любой символ (для ошибок)
    ''', re.VERBOSE | re.IGNORECASE)
    
    tokens = []
    for match in token_pattern.finditer(text):
        token = match.group()
        if token.strip():  # игнорируем пустые токены
            tokens.append(token)
    
    return tokens

def parse_dict(tokens, pos):
    """Парсит словарь: begin ... end"""
    if tokens[pos] != 'begin':
        raise SyntaxError(f"Ожидается 'begin', получено '{tokens[pos]}'")
    
    pos += 1
    result = {}
    
    while pos < len(tokens) and tokens[pos] != 'end':
        # Парсим пару: имя := значение;
        if pos + 3 >= len(tokens):
            raise SyntaxError("Незавершённая пара имя-значение")
        
        name = tokens[pos]
        if not re.match(r'^[a-z]+$', name):
            raise SyntaxError(f"Неверное имя: {name}")
        
        if tokens[pos + 1] != ':=':
            raise SyntaxError(f"Ожидается ':=' после имени '{name}'")
        
        # Парсим значение
        value, pos = parse_value(tokens, pos + 2)
        
        if pos >= len(tokens) or tokens[pos] != ';':
            raise SyntaxError(f"Ожидается ';' после значения для '{name}'")
        
        result[name] = value
        pos += 1
    
    if pos >= len(tokens) or tokens[pos] != 'end':
        raise SyntaxError("Ожидается 'end' для завершения словаря")
    
    return result, pos + 1

def parse_const_expr(tokens, pos):
    """Парсит константное выражение: ^( ... )"""
    if tokens[pos] != '^(':
        raise SyntaxError(f"Ожидается '^(', получено '{tokens[pos]}'")
    
    pos += 1
    stack = []
    
    while pos < len(tokens) and tokens[pos] != ')':
        token = tokens[pos]
        
        # Число
        if token.startswith('0x'):
            stack.append(int(token, 16))
            pos += 1
        
        # Имя (в этом упрощённом варианте имена не поддерживаются в выражениях)
        elif re.match(r'^[a-z]+$', token):
            # Для простоты считаем, что это число 0
            stack.append(0)
            pos += 1
        
        # Операция +
        elif token == '+':
            if len(stack) < 2:
                raise SyntaxError("Недостаточно операндов для '+'")
            b = stack.pop()
            a = stack.pop()
            stack.append(a + b)
            pos += 1
        
        # Операция sqrt
        elif token == 'sqrt':
            if len(stack) < 1:
                raise SyntaxError("Недостаточно операндов для 'sqrt'")
            a = stack.pop()
            stack.append(int(math.sqrt(a)))
            pos += 1
        
        else:
            raise SyntaxError(f"Неизвестный токен в выражении: {token}")
    
    if pos >= len(tokens) or tokens[pos] != ')':
        raise SyntaxError("Ожидается ')' для завершения выражения")
    
    if len(stack) != 1:
        raise SyntaxError("Некорректное выражение")
    
    return stack[0], pos + 1

def parse_value(tokens, pos):
    """Парсит значение (число, словарь или выражение)"""
    if pos >= len(tokens):
        raise SyntaxError("Ожидается значение")
    
    token = tokens[pos]
    
    # Число
    if token.startswith('0x'):
        return int(token, 16), pos + 1
    
    # Словарь
    elif token == 'begin':
        return parse_dict(tokens, pos)
    
    # Константное выражение
    elif token == '^(':
        return parse_const_expr(tokens, pos)
    
    # Имя (в этом упрощённом варианте не поддерживается как значение)
    elif re.match(r'^[a-z]+$', token):
        # Для простоты считаем это ошибкой
        raise SyntaxError(f"Имя '{token}' не может быть значением")
    
    else:
        raise SyntaxError(f"Неверное значение: {token}")

def parse(text):
    """Основная функция парсинга"""
    tokens = tokenize(text)
    if not tokens:
        raise SyntaxError("Входные данные пусты")
    
    result, pos = parse_dict(tokens, 0)
    
    if pos < len(tokens):
        raise SyntaxError(f"Лишние токены в конце: {tokens[pos:]}")
    
    return result

# ==================== XML КОНВЕРТЕР ====================

def dict_to_xml(data, root_name="dict"):
    """Преобразует словарь в XML"""
    if isinstance(data, dict):
        root = ET.Element(root_name)
        for key, value in data.items():
            pair = ET.SubElement(root, "pair")
            pair.set("name", key)
            if isinstance(value, dict):
                pair.append(dict_to_xml(value, root_name))
            else:
                pair.text = str(value)
        return root
    return ET.Element("error")

def prettify_xml(elem):
    """Форматирует XML"""
    rough = ET.tostring(elem, 'utf-8')
    parsed = minidom.parseString(rough)
    return parsed.toprettyxml(indent="  ")

# ==================== ОСНОВНАЯ ПРОГРАММА ====================

def main():
    parser = argparse.ArgumentParser(description='Конвертер в XML')
    parser.add_argument('-o', '--output', required=True, help='Выходной XML файл')
    args = parser.parse_args()
    
    try:
        # Читаем из stdin
        input_text = sys.stdin.read()
        
        if not input_text.strip():
            print("Ошибка: входные данные пусты", file=sys.stderr)
            sys.exit(1)
        
        # Парсим
        data = parse(input_text)
        
        # Конвертируем в XML
        xml_root = dict_to_xml(data)
        pretty_xml = prettify_xml(xml_root)
        
        # Пишем в файл
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        
        print(f"Успешно: {args.output}", file=sys.stderr)
        
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()