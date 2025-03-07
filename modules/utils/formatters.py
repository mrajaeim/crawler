import re


def format_price(price_string, to_int=True):
    cleaned = re.sub(r'[^\d,]', '', price_string)
    number_string = cleaned.replace(',', '')
    try:
        if to_int:
            return int(number_string)
        return float(number_string)
    except ValueError:
        return "N/A"
