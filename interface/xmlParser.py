import importlib
import xml.etree.ElementTree as ET

def parse(filepath: str, parent = None):
    tree = ET.parse(filepath)
    
    root = tree.getroot()
    return getInstance(root, parent)

def getInstance(element: "Element", parent = None):
    tokens = element.tag.split('.')

    # parse tag into an instance
    if len(tokens) > 1:
        m = importlib.import_module(str.join('.', tokens[:-1]))
        component = getattr(m, tokens[-1])(parent=parent)
    else:
        component = globals()[tokens[1]](parent=parent)
    
    # set fields
    for key, value in element.attrib.items():
        # first check for a property
        try:
            prop = getattr(component, key)
            if prop == property:
                prop.fset(component, value)
                continue
        except: pass
        # default fallback
        setattr(component, key, value)

    # populate component with nested elements
    for child in element:
        component.add(getInstance(child))
    
    return component
