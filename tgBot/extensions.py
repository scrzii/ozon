def smet(string: str, end: str="/") -> str:
    """
    String Must Ends with This
    For example:
        Directory must ends with "/"
        This function return:
            smet("/usr/bin/qwe") -> "usr/bin/qwe/"
            smet("/usr/bin/qwe/") -> "usr/bin/qwe/"
    :param string: string raw
    :param end: string must ends width this parameter
    :return: changed string
    """
    return string if string.endswith(end) else string + end
