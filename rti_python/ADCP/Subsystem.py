

BASE_FREQ = 1152000


def ss_frequency(ss_code):
    """
    Get the frequency based subsystem code.
    :param ss_code: Subsystem code.
    :return: Frequency
    """
    if ss_code == "2":                  # 1200 khz
        return BASE_FREQ
    elif ss_code == "3":                # 600 khz
        return BASE_FREQ/2
    elif ss_code == "4":                # 300 khz
        return BASE_FREQ/4
    elif ss_code == "6":                # 1200 khz, 45 degree offset
        return BASE_FREQ
    elif ss_code == "7":                # 600 khz, 45 degree offset
        return BASE_FREQ/2
    elif ss_code == "8":                # 300 khz, 45 degree offset
        return BASE_FREQ/4
    elif ss_code == "A":                # 1200 khz vertical beam
        return BASE_FREQ
    elif ss_code == "B":                # 600 khz vertical beam
        return BASE_FREQ/2
    elif ss_code == "C":                # 300 khz vertical beam
        return BASE_FREQ/4
    elif ss_code == "D":                # 150 khz vertical beam
        return BASE_FREQ/6
    elif ss_code == "E":                # 78 khz vertical beam
        return BASE_FREQ/8
    else:
        return BASE_FREQ                # Default is 1200 khz

def ss_label(ss_code):
    """
    Get the frequency based subsystem code.
    :param ss_code: Subsystem code.
    :return: Frequency
    """
    if ss_code == "2":                  # 1200 khz
        return "1200 kHz"
    elif ss_code == "3":                # 600 khz
        return "600 kHz"
    elif ss_code == "4":                # 300 khz
        return "300 kHz"
    elif ss_code == "6":                # 1200 khz, 45 degree offset
        return "1200 kHz, 45 degree offset"
    elif ss_code == "7":                # 600 khz, 45 degree offset
        return "600 kHz, 45 degree offset"
    elif ss_code == "8":                # 300 khz, 45 degree offset
        return "300 kHz, 45 degree offset"
    elif ss_code == "A":                # 1200 khz vertical beam
        return "1200 kHz vertical beam"
    elif ss_code == "B":                # 600 khz vertical beam
        return "600 kHz vertical beam"
    elif ss_code == "C":                # 300 khz vertical beam
        return "300 kHz vertical beam"
    elif ss_code == "D":                # 150 khz vertical beam
        return "150 kHz vertical beam"
    elif ss_code == "E":                # 78 khz vertical beam
        return "75 kHz vertical beam"
    else:
        return "1200 kHz"                # Default is 1200 khz

