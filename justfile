just := if os_family() == "windows" { "rust-just" } else { "just" }
utils := "./modules/utils"

default:
    {{just}} --list

[group: 'conversion']
x2j input output:
    python {{utils}}/xml_to_json.py {{input}} {{output}}

[group: 'conversion']
imgcv input output:
    python {{utils}}/image_converter.py {{input}} {{output}}

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
clean-cache:
    rm -rf __pycache__ *.pyc .pytest_cache

[group: 'utility']
db-wipe:
    rm data/crawler.db -f
    @echo "DB wiped!"

[group: 'utility']
img-wipe:
    rm data/images -rf
    @echo "Images wiped!"


[group: 'utility']
wipe: db-wipe img-wipe
    @echo "All gathered data wiped!"