from lxml import etree

def validate_schema(input_filename, schema_filename):
    with open(schema_filename) as f:
        schema_xml = etree.XML(f.read())
        schema = etree.XMLSchema(schema_xml)
        parser = etree.XMLParser(schema=schema)
        with open(input_filename) as input_f:
            root = etree.fromstring(input_f.read(), parser)
            return root
