from email.header import Header
from email.header import decode_header
from email.utils import parseaddr

from logHandler import logger


def getSubject(msg):
    """
    解析出邮件标题
    :param msg:
    :return:
    """
    subject = msg.get('Subject', '')
    subject = __decode_str(subject)
    return subject


def getFrom(msg):
    """
    解析出邮件发件人
    :param msg:
    :return:
    """
    value = msg.get('From', '')
    name, _from = parseaddr(value)
    name = __decode_str(name)
    return _from


def getTo(msg):
    """
    解析出邮件收件人列表
    :param msg:
    :return:
    """
    to = []
    value = msg.get('To', '')
    if ',' in value:
        for val in value.split(','):
            _name, _to = parseaddr(val)
            to.append(_to)
            # _name = __decode_str(_name)
    else:
        _name, _to = parseaddr(value)
        to.append(_to)
        # name = __decode_str(name)
    return to


def getDate(msg):
    """
    解析出邮件日期
    :param msg:
    :return:
    """
    _date = msg.get('Date', None)
    if not _date:
        received:str = msg.get("Received",None)
        if received:
            return received.split(";")[-1]
    return _date


def getContent(msg, indent=0):
    """
    解析出邮件正文
    :param msg:
    :param indent:
    :return:
    """
    if msg.is_multipart():
        parts = msg.get_payload()
        _result = ''
        for n, part in enumerate(parts):
            # print('%spart %s' % ('  ' * indent, n))
            # print('%s--------------------' % ('  ' * indent))
            _result += getContent(part, indent + 1)
        return _result
    else:
        content_type = msg.get_content_type()
        if content_type == 'text/plain' or content_type == 'text/html':
            content = msg.get_payload(decode=True)
            charset = __guess_charset(msg)
            if charset:
                content = content.decode(charset)
            # print('%sText: %s' % ('  ' * indent, content + '...'))
            return content
        else:
            # print('%sAttachment: %s' % ('  ' * indent, content_type))
            pass
    return ''


def getAttach(msg, filePath):
    """
    解析出邮件附件
    :param msg:
    :param filePath:
    :return:
    """
    attachmentFiles = []
    for part in msg.walk():
        file_name = part.get_filename()  # 获取附件名称类型
        contType = part.get_content_type()
        logger.debug(contType)

        if file_name:
            h = Header(file_name)
            dh = decode_header(h)  # 对附件名称进行解码
            filename = dh[0][0]
            if dh[0][1]:
                filename = __decode_str(str(filename, dh[0][1]))  # 将附件名称可读化
                logger.debug(filename)
            data = part.get_payload(decode=True)  # 下载附件
            att_file = open(filePath + filename, 'wb')  # 在指定目录下创建文件，注意二进制文件需要用wb模式打开
            attachmentFiles.append(filename)
            att_file.write(data)  # 保存附件
            att_file.close()
    return attachmentFiles


# indent用于缩进显示:
def print_info(msg, indent=0):
    if indent == 0:
        for header in ['From', 'To', 'Subject']:
            value = msg.get(header, '')
            if value:
                if header == 'Subject':
                    value = __decode_str(value)
                else:
                    hdr, addr = parseaddr(value)
                    name = __decode_str(hdr)
                    value = u'%s <%s>' % (name, addr)
            logger.debug('%s%s: %s' % ('  ' * indent, header, value))
    if msg.is_multipart():
        parts = msg.get_payload()
        for n, part in enumerate(parts):
            logger.debug('%spart %s' % ('  ' * indent, n))
            logger.debug('%s--------------------' % ('  ' * indent))
            print_info(part, indent + 1)
    else:
        content_type = msg.get_content_type()
        if content_type == 'text/plain' or content_type == 'text/html':
            content = msg.get_payload(decode=True)
            charset = __guess_charset(msg)
            if charset:
                content = content.decode(charset)
            logger.debug('%sText: %s' % ('  ' * indent, content + '...'))
        else:
            logger.debug('%sAttachment: %s' % ('  ' * indent, content_type))


def __decode_str(s):
    decode_header(s)
    value, charset = decode_header(s)[0]
    if charset:
        value = value.decode(charset)
    return value


def __decode_strs(s):
    decode_header(s)
    value, charset = decode_header(s)
    if charset:
        value = value.decode(charset)
    return value


def __guess_charset(msg):
    charset = msg.get_charset()
    if charset is None:
        content_type = msg.get('Content-Type', '').lower()
        pos = content_type.find('charset=')
        if pos >= 0:
            charset = content_type[pos + 8:].strip()
    return charset
