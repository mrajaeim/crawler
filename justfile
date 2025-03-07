just := if os_family() == "windows" { "rust-just" } else { "just" }
utils := "./modules/utils"
# Default help message
default:
    {{just}} --list

[group: 'conversion']
x2j input output:
    python {{utils}}/xml_to_json.py {{input}} {{output}}

[group: 'development']
install:
    poetry install

[group: 'development']
format:
    black .

[group: 'development']
lint:
    flake8 .

[group: 'development']
test:
    pytest

[group: 'utility']
clean:
    rm -rf __pycache__ *.pyc .pytest_cache
