#
#  dotfiles
#  Copyright © 2026 Space Code. All rights reserved.
#

import lldbbase as bc


def commands():
    """Return a list of custom LLDB commands registered in the plugin"""
    return [UDumpCommand()]


class UDumpCommand(bc.BaseCommand):
    "UDumpCommand"

    def name(self):
        """The command name used in LLDB (e.g. (lldb) udump)"""
        return "udump"

    def description(self):
        return "Dumps NSUserDefaults contents as a formatted key-value table"

    def options(self):
        return [
            bc.CommandArgument(
                short="-s",
                long="--suite",
                arg="suite",
                type="string",
                default="",
                help="Suite name for initWithSuiteName: (default: standardUserDefaults)",
            ),
            bc.CommandArgument(
                short="-f",
                long="--filter",
                arg="filter",
                type="string",
                default="",
                help="Show only keys containing this substring (case-intensive)",
            ),
            bc.CommandArgument(
                short="-o",
                long="--alphabetical",
                arg="alphabetical",
                boolean=True,
                default=False,
                help="Sort keys alphabetically",
            ),
        ]

    def run(self, args, options):
        defaults = get_defaults_instance(options.suite)

        if defaults is None or defaults == "0x0":
            label = options.suite or "standardUserDefaults"
            print(f"error: could not get NSUserDefaults instance ({label})")
            return

        entries = collect_entries(defaults, options.filter)

        if options.alphabetical:
            entries.sort(key=lambda x: x[0].lower())

        label = options.suite or "standardUserDefaults"
        print_table(entries, label, options.filter)


def get_defaults_instance(suite):
    """
    Returns the NSUserDefaults instance address for the given suite name.
    Uses standardUserDefaults when suite is empty.
    :param suite: Suite name string, or empty string for standard defaults
    :return: Object address string (e.g. '0x600003a12340'), or None on failure
    """

    if suite:
        return bc.evaluate_expression(
            f'(id)[[NSUserDefaults alloc] initWithSuiteName:@"{suite}"]'
        )
    return bc.evaluate_expression("(id)[NSUserDefaults standardUserDefaults]")


def get_dictionary_representation(defaults):
    """
    Calls dictionaryRepresentation on an NSUserDefaults instance.
    Returns an NSDictionary containing all currently registered key-value pairs.
    :param defaults: NSUserDefaults address string
    :return: NSDictionary address string
    """

    return bc.evaluate_expression(
        f"(id)[(NSUserDefaults *){defaults} dictionaryRepresentation]"
    )


def collect_entries(defaults, filter_str):
    """
    Iterates over all keys in NSUserDefaults and returns a list of (key, value) tuples.
    Applies case-insensitive substring filtering when filter_str is non-empty.
    :param defaults: NSUserDefaults address string
    :param filter_str: Substring to filter keys by, or empty string to include all
    :return: List of (key_string, value_string) tuples
    """

    dictionary = get_dictionary_representation(defaults)

    keys = bc.evaluate_expression(f"(id)[(NSDictionary *){dictionary} allKeys]")
    count = bc.evaluate_integer_expression(f"[(NSArray *){keys} count]")

    entries = []

    for i in range(count):
        key_obj = bc.evaluate_expression(f"(id)[(NSArray *){keys} objectAtIndex:{i}]")
        key_str = nsstring_to_str(key_obj)

        if filter_str and filter_str.lower() not in key_str.lower():
            continue

        val_obj = bc.evaluate_expression(
            f"(id)[(NSDictionary *){dictionary} objectForKey:(id){key_obj}]"
        )

        val_str = format_value(val_obj)

        entries.append((key_str, val_str))

    return entries


def nsstring_to_str(obj):
    """
    Converts an NSString object address to a Python string via UTF8String.
    :param obj: NSString address string
    :return: Python string, or '<nil>' / '<unreadable>' on failure
    """

    if obj is None or obj == "0x0":
        return "<nil>"

    value = bc.evaluate_expression_value(
        f"(const char *)[(NSString *){obj} UTF8String]"
    )

    summary = value.GetSummary()

    if summary:
        return summary.strip('"')
    return "<unreadable>"


def get_class_name(obj):
    """
    Returns the class name of any ObjC object — including tagged pointers.

    NSStringFromClass([(id)ptr class]) fails in two situations:
      1. Tagged pointers — no real heap object, ObjC dispatch crashes.
      2. Certain toll-free bridged types — LLDB loses type info on (id) cast.

    object_getClassName((id)ptr) is a plain C function from <objc/runtime.h>
    that handles both cases via the ObjC runtime directly, without message send.
    We cast the return to (const char *) because LLDB doesn't import the header
    and treats the return type as unknown otherwise.

    :param obj: Object address string (e.g. '0x600003a12340')
    :return: Class name string, or '<unknown>' on failure
    """
    value = bc.evaluate_expression_value(
        f"(const char *)object_getClassName((id){obj})"
    )
    summary = value.GetSummary()
    if summary:
        return summary.strip('"')
    return "<unknown>"


def format_value(obj):
    """
    Formats an arbitrary NSObject for display.
    Appends the short class name in parentheses to disambiguate types
    (e.g. '1  (Bool)' vs '1  (Number)').
    :param obj: Object address string
    :return: Formatted string representation
    """
    if obj is None or obj == "0x0":
        return "nil"

    class_name = get_class_name(obj)
    description = nsstring_to_str(
        bc.evaluate_expression(f"(id)[(NSObject *){obj} description]")
    )

    short = shorten_class_name(class_name)
    return f"{description}  ({short})"


def shorten_class_name(class_name):
    """
    Strips common Objective-C cluster prefixes for readability.
    E.g. '__NSCFBoolean' -> 'Bool', '__NSCFString' -> 'String'.
    :param class_name: Full ObjC class name string
    :return: Shortened display name
    """

    replacements = {
        "__NSCFBoolean": "Bool",
        "__NSCFString": "String",
        "__NSCFNumber": "Number",
        "__NSCFArray": "Array",
        "__NSCFDictionary": "Dictionary",
        "__NSTaggedDate": "Date",
        "NSConcreteMutableData": "Data",
    }

    return replacements.get(class_name, class_name)


def is_tagged_pointer(obj):
    """
    Returns True if obj is an Objective-C tagged pointer.
    On arm64, tagged pointers have the most significant bit (bit 63) set.
    They store the value inline in the pointer — no heap object exists,
    so ObjC message sends via LLDB expression evaluation fail with
    'no known method' errors.
    :param obj: Object address string (e.g. '0xbcc1f272952fc4b8')
    :return: bool
    """
    try:
        return bool((int(obj, 16) >> 63) & 1)
    except (TypeError, ValueError):
        return False


def print_table(entries, label, filter_str):
    """
    Prints the key-value pairs as a formatted ASCII table.
    :param entries: List of (key, value) tuples
    :param label: Display name for the NSUserDefaults instance
    :param filter_str: Active filter string (shown in footer when non-empty)
    """
    if not entries:
        hint = f" (filter: '{filter_str}')" if filter_str else ""
        print(f"\n  {label}: no keys found{hint}\n")
        return

    max_key_len = min(max(len(k) for k, _ in entries), 50)
    sep = "─" * (max_key_len + 2) + "┼" + "─" * 46

    print(f"\n  NSUserDefaults: {label}")
    print(f"  {sep}")
    print(f"  {'KEY':<{max_key_len}}  │  VALUE")
    print(f"  {sep}")

    for key, value in entries:
        display_key = key[:max_key_len]
        display_val = value[:80] + ("…" if len(value) > 80 else "")
        print(f"  {display_key:<{max_key_len}}  │  {display_val}")

    print(f"  {sep}")
    footer = f"  {len(entries)} keys"
    if filter_str:
        footer += f"  (filter: '{filter_str}')"
    print(footer)
    print()
