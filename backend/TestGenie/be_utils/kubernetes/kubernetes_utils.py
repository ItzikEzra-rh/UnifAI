def parse_k8s_command(output):
    """

    :param output: output of k8s normal command
    :return: list that contains lists, every element in the list is as in the line of output the command
    example:
    -----------------------------------input------------------------------------------------------------
    NAMESPACE           NAME                                   READY   UP-TO-DATE   AVAILABLE   AGE
    gatekeeper-system   gatekeeper-audit                       1/1     1            1           40d
    -----------------------------------output-----------------------------------------------------------
    [['NAMESPACE', 'NAME', 'READY', 'UP-TO-DATE', 'AVAILABLE', 'AGE'],
    ['gatekeeper-system', 'gatekeeper-audit', '1/1', '1', '1', '40d']]

    """
    return [[elem for elem in line.split(' ') if elem.strip()] for line in output.split('\n') if
            line.strip()]


def parse_k8s_version(data):
    data = [line for line in data.split('\n') if line.strip()]
    for line in data:
        if 'server' in line.lower():
            version = line.split(':')[1].strip()
            version = '.'.join(version.split('.')[:2]) if len(version.split('.')) > 1 else version
            return version
    return ''
