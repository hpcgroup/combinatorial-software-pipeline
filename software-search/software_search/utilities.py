
# https://stackoverflow.com/a/36019241/3769237
def is_sequence(x):
    return (not hasattr(x, "strip") and
            hasattr(x, "__iteritems__") or
            hasattr(x, "__iter__"))

# see https://stackoverflow.com/a/36019241/3769237
def listify(x):
    if is_sequence(x) and not isinstance(x, dict):
        return x
    return [x,]