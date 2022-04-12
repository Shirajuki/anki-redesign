def module_exists(module_name):
    try:
        __import__(module_name)
    except ImportError:
        return False
    else:
        return True

def module_has_attribute(module_name, attribute):
    if module_exists(module_name):
        return hasattr(__import__(module_name), attribute)
    return False

def attribute_exists(object, attribute):
    return attribute in object.__dict__

def context_name_includes(context, classname):
    return classname in str(context.__class__)