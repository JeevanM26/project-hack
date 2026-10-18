# test_suite.py

import pytest

@pytest.fixture
def load_html():
    # Load the HTML page (replace with your actual method)
    return '<!DOCTYPE html> ... ' 

def test_page_loads(load_html):
    assert 'Simple Calculator' in load_html
def test_input_fields(load_html):
    assert 'Enter first number' in load_html
    assert 'Enter second number' in load_html
def test_calculate_button(load_html):
    assert 'Calculate Sum' in load_html
def test_result_area(load_html):
    assert 'Sum:' in load_html