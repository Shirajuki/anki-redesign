def module_exists(module_name):
    try:
        __import__(module_name)
    except ImportError:
        return False
    else:
        return True

def attribute_exists(object, attribute):
    return attribute in object.__dict__