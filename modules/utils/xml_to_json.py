import xml.etree.ElementTree as ET
import json
import argparse

def xml_to_dict(element):
    """
    Recursively convert an XML element to a dictionary.
    """
    # If the element has no children, return its text
    if not list(element):
        return element.text

    # Create a dictionary to hold the element's data
    data = {}
    for child in element:
        # If the child tag is already in the dictionary, convert it to a list
        if child.tag in data:
            if not isinstance(data[child.tag], list):
                data[child.tag] = [data[child.tag]]
            data[child.tag].append(xml_to_dict(child))
        else:
            data[child.tag] = xml_to_dict(child)

    # Add attributes if any
    if element.attrib:
        data['@attributes'] = element.attrib

    return data

def xml_to_json(xml_string):
    """
    Convert an XML string to a JSON string.
    """
    # Parse the XML string
    root = ET.fromstring(xml_string)

    # Convert the XML to a dictionary
    data_dict = xml_to_dict(root)

    # Convert the dictionary to a JSON string
    json_string = json.dumps(data_dict, indent=4)

    return json_string

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Convert an XML file to a JSON file.")
    parser.add_argument("input_file", help="Path to the input XML file")
    parser.add_argument("output_file", help="Path to the output JSON file")
    args = parser.parse_args()

    # Read the XML file
    with open(args.input_file, "r") as xml_file:
        xml_data = xml_file.read()

    # Convert XML to JSON
    json_data = xml_to_json(xml_data)

    # Write the JSON data to the output file
    with open(args.output_file, "w") as json_file:
        json_file.write(json_data)

    print(f"JSON data has been saved to {args.output_file}")

if __name__ == "__main__":
    main()