#!/usr/bin/env python3
"""Тесты для упрощённого конвертера"""

import sys
import os
import tempfile
from io import StringIO
from simple_converter import parse, dict_to_xml, prettify_xml
import xml.etree.ElementTree as ET

def test_parse_simple():
    """Тест простого парсинга"""
    text = "begin x := 0xA; y := 0xB; end"
    result = parse(text)
    assert result == {'x': 10, 'y': 11}
    print("✓ Простой парсинг OK")

def test_parse_nested():
    """Тест вложенного словаря"""
    text = """
    begin
      outer := begin
        inner := 0xFF;
      end;
    end
    """
    result = parse(text)
    assert result == {'outer': {'inner': 255}}
    print("✓ Вложенный словарь OK")

def test_parse_const_expr():
    """Тест константных выражений"""
    text = "begin result := ^(0xA 0x5 +); end"
    result = parse(text)
    assert result == {'result': 15}  # 10 + 5
    print("✓ Константное выражение (+) OK")
    
    text = "begin result := ^(0x64 sqrt); end"
    result = parse(text)
    assert result == {'result': 10}  # sqrt(100)
    print("✓ Константное выражение (sqrt) OK")

def test_parse_comments():
    """Тест комментариев"""
    text = """
    --[[ Это комментарий ]]
    begin
      value := 0x2A;  --[[ ещё комментарий ]]--
    end
    """
    result = parse(text)
    assert result == {'value': 42}
    print("✓ Комментарии OK")

def test_xml_generation():
    """Тест генерации XML"""
    data = {'name': 16, 'nested': {'value': 255}}
    xml_root = dict_to_xml(data)
    
    # Проверяем структуру
    assert xml_root.tag == 'dict'
    pairs = list(xml_root)
    assert len(pairs) == 2
    
    # Проверяем первый элемент
    assert pairs[0].get('name') == 'name'
    assert pairs[0].text == '16'
    
    # Проверяем вложенность
    nested_pair = pairs[1]
    assert nested_pair.get('name') == 'nested'
    nested_dict = nested_pair.find('dict')
    assert nested_dict is not None
    
    print("✓ Генерация XML OK")

def test_error_handling():
    """Тест обработки ошибок"""
    test_cases = [
        ("begin x := 0xG; end", "шестнадцатеричное"),  # неверное число
        ("begin x := 0xA end", ";"),  # нет точки с запятой
        ("begin 123 := 0xA; end", "имя"),  # неверное имя
        ("x := 0xA;", "begin"),  # нет begin
        ("begin x := 0xA;", "end"),  # нет end
    ]
    
    for text, expected_error in test_cases:
        try:
            parse(text)
            assert False, f"Ожидалась ошибка для: {text}"
        except Exception as e:
            error_msg = str(e).lower()
            if expected_error.lower() not in error_msg:
                print(f"Для '{text}' ожидалась ошибка с '{expected_error}', получено: {error_msg}")
            else:
                print(f"✓ Ошибка '{expected_error}' корректно обработана")

def run_all_tests():
    """Запускает все тесты"""
    print("Запуск тестов...\n")
    
    tests = [
        test_parse_simple,
        test_parse_nested,
        test_parse_const_expr,
        test_parse_comments,
        test_xml_generation,
        test_error_handling,
    ]
    
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ Тест не пройден: {e}")
        except Exception as e:
            print(f"✗ Ошибка в тесте: {e}")
    
    print("\nТестирование завершено!")

if __name__ == "__main__":
    run_all_tests()