import inspect
import re
import shlex
import types
from typing import Annotated, Any, Callable, List, Union, get_args, get_origin

from .state import ConnectionState
from .user import User, PartialUser
from .messages import Message

def simple_tokenize(text: str) -> list[str]:
    tokens = []
    current = []
    in_quotes = False
    escape = False

    for char in text:
        if escape:
            current.append(char)
            escape = False
        elif char == "\\":
            escape = True
        elif char == '"':
            in_quotes = not in_quotes
        elif char.isspace() and not in_quotes:
            if current:
                tokens.append("".join(current))
                current = []
        else:
            current.append(char)

    if current:
        tokens.append("".join(current))

    return tokens

class Greedy:
    """Marker type for Annotated[..., Greedy]"""
    pass

def is_list_type(ann):
    return get_origin(ann) in (list, List)

def get_list_arg_type(ann):
    return get_args(ann)[0] if get_args(ann) else str

async def cast_type(typ: type, raw: str, connection_state: ConnectionState) -> Any:
    if typ is str:
        return raw
    if typ is int:
        return int(raw)
    if typ is float:
        return float(raw)
    if typ is bool:
        return raw.lower() in ("1", "true", "yes", "y", "t")
    if typ is User:
        mention = re.fullmatch(r"@user:(\d+)", raw)
        if mention:
            user_id = int(mention.group(1))
            # fetch by ID from the mention
            return await PartialUser(user_id, None)\
                        .attach_state(connection_state)\
                        .fetch()
        try:
            return await PartialUser(int(raw), None)\
                        .attach_state(connection_state)\
                        .fetch()
        except ValueError:
            # not a numeric ID, try username below
            pass
        return await PartialUser(None, raw)\
                    .attach_state(connection_state)\
                    .fetch_by_username()
    raise ValueError(f"Unsupported type: {typ!r}")

def is_union_type(ann):
    """"""
    return (
        get_origin(ann) is Union
        or isinstance(ann, types.UnionType)  # for Python 3.10+'s X|Y
    )

def is_annotated_greedy(ann):
    if get_origin(ann) is Annotated:
        _, *annotations = get_args(ann)
        return any(isinstance(a, Greedy) or a is Greedy for a in annotations)
    return False

def get_annotated_base(ann):
    if get_origin(ann) is Annotated:
        return get_args(ann)[0]
    return ann

async def parse_args(func: Callable, input_str: str, message: Message, connection_state: ConnectionState) -> list:
    """Parses the arguments for a command.

    Args:
        func (Callable): The function to parse the args for.
        input_str (str): The list of arguments in string form, e.g. "1 2 3".
        message (Message): A message object.

    Raises:
        SyntaxError: If two message parameters are requested.
        ValueError: If a required parameter is not defined.

    Returns:
        list: A list of arguments to be provided to the function.
    """
    
    sig = inspect.signature(func)
    params = list(sig.parameters.values())
    # Bypasses for simple functions so it doesn't always need to pass the whole thing in
    if len(params) == 0:
        return []
    if len(params) == 1:
        ann = get_args(params[0].annotation)
        if ann is Message or (is_union_type(ann) and Message in args):
            return [message]
    tokens = simple_tokenize(input_str)
    out_args = []
    idx = 0
    message_injected = False

    for p_i, param in enumerate(params):
        ann = param.annotation
        origin = get_origin(ann)
        args = get_args(ann)

        if ann is Message or (is_union_type(ann) and Message in args):
            if message_injected:
                # Second message not allowed unless it's optional [in which case we just give None instead]
                if origin is Union and type(None) in args:
                    out_args.append(None)
                    continue
                raise SyntaxError(f"Multiple Message parameters not allowed: {param.name}")
            out_args.append(message)
            message_injected = True
            continue

        if is_annotated_greedy(ann):
            base_type = get_annotated_base(ann)
            needed_for_rest = len(params) - (p_i + 1)
            take = max(0, len(tokens) - idx - needed_for_rest)
            raw = " ".join(tokens[idx: idx + take])
            idx += take
            out_args.append(await cast_type(base_type, raw, connection_state))
            continue
        
        if is_list_type(ann):
            elem_type = get_list_arg_type(ann)
            needed_for_rest = len(params) - (p_i + 1)
            take = max(0, len(tokens) - idx - needed_for_rest)
            items = tokens[idx: idx + take]
            idx += take
            out_args.append([await cast_type(elem_type, item, connection_state) for item in items])
            continue

        if idx >= len(tokens):
            if param.default is not inspect.Parameter.empty:
                out_args.append(param.default)
                continue
            if is_union_type(ann) and type(None) in args:
                out_args.append(None)
                continue
            raise ValueError(f"Missing value for parameter '{param.name}'")

        raw = tokens[idx]
        idx += 1

        if is_union_type(ann) and type(None) in args:
            if raw.lower() == "none":
                out_args.append(None)
            else:
                non_none = next(t for t in args if t is not type(None))
                out_args.append(await cast_type(non_none, raw, connection_state))
        else:
            out_args.append(await cast_type(ann, raw, connection_state))

    return out_args