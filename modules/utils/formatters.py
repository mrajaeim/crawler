import re


def format_price(price_string, to_int=True):
    cleaned = re.sub(r'[^\d,]', '', price_string)
    number_string = cleaned.replace(',', '')
    try:
        if to_int:
            return str(int(number_string))
        return str(float(number_string))
    except ValueError:
        return "N/A"
