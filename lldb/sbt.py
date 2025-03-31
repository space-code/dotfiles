"""
LLDB Symbolicate Script

This script provides an LLDB command to symbolicate stripped backtraces,
particularly for Objective-C code. It helps resolve symbols in stack traces
that would otherwise be difficult to interpret in stripped executables.
"""

import lldb
import os
import shlex
import optparse


def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand("command script add -f sbt.handle_command sbt")


def handle_command(debugger, command, result, internal_dict):
    """
    Symbolicate backtrace. Will symbolicate a stripped backtrace
    from an executable if the backtrace is using Objective-C
    code. Currently doesn't work on aarch64 stripped executables
    but works great on x64 :]
    """
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    if thread is None:
        result.SetError("LLDB must be paused to execute this command")
        return

    frame_addresses = [f.addr.GetLoadAddress(target) for f in thread.frames]

    frame_string = process_stack_trace_string_from_addresses(frame_addresses, target)

    result.AppendMessage(frame_string)


def process_stack_trace_string_from_addresses(frame_addresses, target):
    """
    Processes stack trace addresses and attempts to resolve function names,
    handling cases where symbols are stripped.
    """
    frame_string = ""
    start_addresses = [
        target.ResolveLoadAddress(f).symbol.addr.GetLoadAddress(target)
        for f in frame_addresses
    ]
    script = generate_executable_methods_script(start_addresses)

    methods = target.EvaluateExpression(script, generate_options())
    methods_val = lldb.value(methods.deref)

    # Enumerate each of the SBFrames in address list
    for index, frame_addr in enumerate(frame_addresses):
        addr = target.ResolveLoadAddress(frame_addr)
        symbol = addr.symbol

        if symbol.synthetic:
            children = methods_val.sbvalue.GetNumChildren()
            name = symbol.name + r" ... unresolved womp womp"

            load_address = symbol.addr.GetLoadAddress(target)

            for i in range(children):
                key = int(methods_val[i].key.sbvalue.description)

                if key == load_address:
                    name = methods_val[i].value.sbvalue.description
                    break
        else:
            name = symbol.name

        offset_str = ""
        offset = addr.GetLoadAddress(target) - addr.symbol.addr.GetLoadAddress(target)
        if offset > 0:
            offset_str = f"+ {offset}"

        frame_string += f"frame #{index:<2}: {hex(addr.GetLoadAddress(target))} {addr.module.file.basename}`{name} {offset_str}\n"

    return frame_string


def generate_options():
    """
    Configures LLDB expression evaluation options for Objective-C++ symbolication.
    """
    expr_options = lldb.SBExpressionOptions()
    expr_options.SetUnwindOnError(True)
    expr_options.SetLanguage(lldb.eLanguageTypeObjC_plus_plus)
    expr_options.SetCoerceResultToId(False)
    return expr_options


def generate_executable_methods_script(frame_addresses):
    """
    Generates an Objective-C script that extracts method names for stripped symbols
    using runtime introspection.
    """
    frame_addr_str = "NSArray *ar = @["
    for f in frame_addresses:
        frame_addr_str += '@"' + str(f) + '",'

    frame_addr_str = frame_addr_str[:-1]
    frame_addr_str += "];"

    command_script = r"""
    @import ObjectiveC;
    @import Foundation;
  NSMutableDictionary *retdict = [NSMutableDictionary dictionary];
  unsigned int count = 0;
  const char *path = (char *)[[[NSBundle mainBundle] executablePath] UTF8String];
  const char **allClasses = (const char **)objc_copyClassNamesForImage(path, &count);
  for (int i = 0; i < count; i++) {
    Class cls = objc_getClass(allClasses[i]);
    if (!(Class)class_getSuperclass(cls)) {
      continue;
    }
    unsigned int methCount = 0;
    Method *methods = class_copyMethodList(cls, &methCount);
    for (int j = 0; j < methCount; j++) {
      Method meth = methods[j];
      id implementation = (id)method_getImplementation(meth);
      NSString *methodName = [[[[@"-[" stringByAppendingString:NSStringFromClass(cls)] stringByAppendingString:@" "] stringByAppendingString:NSStringFromSelector(method_getName(meth))] stringByAppendingString:@"]"];
      [retdict setObject:methodName forKey:(id)[@((uintptr_t)implementation) stringValue]];
    }
    
    unsigned int classMethCount = 0;
    
    Method *classMethods = class_copyMethodList(objc_getMetaClass(class_getName(cls)), &classMethCount);
    for (int j = 0; j < classMethCount; j++) {
      Method meth = classMethods[j];
      id implementation = (id)method_getImplementation(meth);
      NSString *methodName = [[[[@"+[" stringByAppendingString:NSStringFromClass(cls)] stringByAppendingString:@" "] stringByAppendingString:NSStringFromSelector(method_getName(meth))] stringByAppendingString:@"]"];
      [retdict setObject:methodName forKey:(id)[@((uintptr_t)implementation) stringValue]];
    }
    
    free(methods);
    free(classMethods);
  }
  free(allClasses);
  """
    command_script += frame_addr_str
    command_script += r"""

  NSMutableDictionary *stackDict = [NSMutableDictionary dictionary];
  [retdict keysOfEntriesPassingTest:^BOOL(id key, id obj, BOOL *stop) {
    
    if ([ar containsObject:key]) {
      [stackDict setObject:obj forKey:key];
      return YES;
    }
    
    return NO;
  }];
  stackDict;
  """
    return command_script
