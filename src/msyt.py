"""Utils for processing myst text resources (in YAML format)"""

import util as u

locale_map = {
    "en-US": "USen",
    "ja-JP": "JPja",
    "de-DE": "EUde",
    "es-ES": "EUes",
    "it-IT": "EUit",
    "fr-FR": "EUfr",
    "ru-RU": "EUru",
    "zh-CN": "CNzh",
    "zh-TW": "TWzh",
    "ko-KR": "KRko",
    "nl-NL": "EUnl",
}

def parse_localization(data: dict, allow_attr: bool) -> tuple[str, str, str | None]:
    """
    Parse localization entry

    Return text, attr, error
    """
    err = u.ensure(isinstance(data, dict) and "contents" in data and len(data) == 1, "Localization data must have 'contents'")
    if err: return "", "", err

    contents = data["contents"]
    text = ""
    attr = ""
    last_control = None

    for x in contents:
        if "text" in x:
            if last_control:
                text += x["text"][last_control:]
                last_control = None
            else:
                text += x["text"]
            continue
        err = u.ensure("control" in x and len(x) == 1, f"entry must have either text or control")
        if err: return "", "", err
        c = x["control"]
        err = u.ensure("kind" in c and isinstance(c["kind"], str), f"control must have kind")
        kind = c["kind"]
        if kind == "raw":
            if "zero" in c:
                # katakana marking above kanji
                try:
                    last_control = c["zero"]["zero"]["field_3"] 
                except KeyError:
                    return "", "", f"failed to parse control"
        
                # divided by 2 because it's in bytes
                err = u.ensure(last_control % 2 == 0, "odd number of bytes to remove")
                if err: return "", "", err
                last_control = last_control // 2
                continue

            if "two" in c:
                # effect and effect description placeholder
                one_field_value = c["two"]["one_field"][0]
                if one_field_value == 7:
                    text += "{{effect}}"
                elif one_field_value == 8:
                    text += "{{effect_desc}}"
                elif one_field_value == 13:
                    text += "{{modifier_value}}"
                else:
                    return "", "", f"invalid two.one_field0: {one_field_value}"
                continue

            if "two_hundred_one" in c:
                # See exefs/main/sub_7100AA4B4C
                if allow_attr:
                    err = u.ensure("dynamic" in c["two_hundred_one"], "two_hundred_one must have dynamic")
                    if err: return "", "", err
                    dynamic = c["two_hundred_one"]["dynamic"]
                    err = u.ensure("field_2" in dynamic[1])
                    if err: return "", "", err
                    v = dynamic[1]["field_2"]
                    err = u.ensure(len(v) == 4, "dynamic field_2 must have 4 elements")
                    if err: return "", "", err
                    plural = v[3]
                    err = u.ensure(plural == 0 or plural == 1, "plural must be 0 or 1")
                    if err: return "", "", err
                    plural = plural == 1
                    if v[0] == 0:
                        t = ""
                    elif v[0] == 1:
                        t = "masculine"
                    elif v[0] == 2:
                        t = "feminine"
                    elif v[0] == 3:
                        t = "neuter"
                    else:
                        return "", "", f"invalid dynamic field_2: {v}"
                    if plural:
                        attr = "plural"
                    else:
                        attr = t
                continue

            return "", "", f"invalid raw control: {c}"

    return text, attr, None

