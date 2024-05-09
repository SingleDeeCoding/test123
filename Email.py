import datetime
import email
import imaplib
import os
import poplib
import re
import smtplib
import socket
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.parser import Parser
from email.utils import parseaddr, formataddr

import EmailDecoder
# from Decorator import decrypt_params
# from DesCode import decrypt_helper
from logHandler import logger


class NEW_POP3(poplib.POP3):
    def __init__(self, host, port=poplib.POP3_PORT, timeout=socket._GLOBAL_DEFAULT_TIMEOUT) -> None:
        super().__init__(host, port, timeout)

    def _getresp(self):
        """重写POP3类的_getresp方法

        Returns:
            _description_
        """
        resp, o = self._getline()
        if self._debugging > 1:
            print('*resp*', repr(resp))
        if not resp.startswith(b'+'):
            """
            # 这行是poplib源码的处理方式: 读取到数据不是+开头就报错 bug#805
            raise error_proto(resp)
            """
            self._getresp()
        return resp

    def _getline(self):
        """重写POP3类的_getline方法

        Raises:
            error_proto: _description_

        Returns:
            _description_
        """
        line = self.file.readline(poplib._MAXLINE + 1)
        """
        # 这里是poplib源码的处理方式: 超出最大行数就报错
        if len(line) > _MAXLINE:
            raise error_proto('line too long')
        """
        if self._debugging > 1:
            print('*get*', repr(line))
        if not line:
            raise poplib.error_proto('-ERR EOF')
        octets = len(line)
        # server can send any combination of CR & LF
        # however, 'readline()' returns lines ending in LF
        # so only possibilities are ...LF, ...CRLF, CR...LF
        if line[-2:] == poplib.CRLF:
            return line[:-2], octets
        if line[:1] == poplib.CR:
            return line[1:-1], octets
        return line[:-1], octets


try:
    import ssl
    HAVE_SSL = True
except ImportError:
    HAVE_SSL = False


class NEW_POP3_SSL(NEW_POP3):
    """POP3 client class over SSL connection

    Instantiate with: POP3_SSL(hostname, port=995, keyfile=None, certfile=None,
                               context=None)

           hostname - the hostname of the pop3 over ssl server
           port - port number
           keyfile - PEM formatted file that contains your private key
           certfile - PEM formatted certificate chain file
           context - a ssl.SSLContext

    See the methods of the parent class POP3 for more documentation.
    """

    def __init__(self, host, port=poplib.POP3_SSL_PORT, keyfile=None, certfile=None,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT, context=None):
        if context is not None and keyfile is not None:
            raise ValueError("context and keyfile arguments are mutually "
                             "exclusive")
        if context is not None and certfile is not None:
            raise ValueError("context and certfile arguments are mutually "
                             "exclusive")
        if keyfile is not None or certfile is not None:
            import warnings
            warnings.warn("keyfile and certfile are deprecated, use a "
                          "custom context instead", DeprecationWarning, 2)
        self.keyfile = keyfile
        self.certfile = certfile
        if context is None:
            context = ssl._create_stdlib_context(certfile=certfile,
                                                 keyfile=keyfile)
        self.context = context
        NEW_POP3.__init__(self, host, port, timeout)

    def _create_socket(self, timeout):
        sock = NEW_POP3._create_socket(self, timeout)
        sock = self.context.wrap_socket(sock,
                                        server_hostname=self.host)
        return sock

    def stls(self, keyfile=None, certfile=None, context=None):
        """The method unconditionally raises an exception since the
        STLS command doesn't make any sense on an already established
        SSL/TLS session.
        """
        raise poplib.error_proto('-ERR TLS session already established')


def send(account, passwd, to, subject, content, server,
         cc=None, bcc=None, isHTML=False, attachFile=None, port: int=25, isSSL=False,
         timeout=30000):
    """
    发送邮件（SMTP）
    :param account: 发送人账号
    :param passwd: 发送人密码
    :param to: 收件人 或 收件人列表
    :param subject: 主题
    :param content: 正文
    :param server: SMTP服务器地址
    :param cc: 抄送
    :param bcc: 密送
    :param isHTML: 是否HTML格式
    :param attachFile: 附件 或 附件列表
    :param port: SMTP邮件服务器端口
    :param isSSL: 是否加密
    :param timeout: 最长等待时间（毫秒）
    :return: 是否发送成功?
    """
    # 判断account类型
    if '<' in account and account.endswith('>'):
        name, account = parseaddr(account)
        fromAccount = formataddr((Header(name, 'utf-8').encode(), account))
    else:
        fromAccount = account

    suc = False
    sev = None
    logger.debug("正在发送邮件...")
    ptn = r'<[\w]+>.*?</[\w]+>'
    isHTML = re.findall(ptn, content)
    if isHTML:
        mimeText = MIMEText(content, 'html', 'utf-8')
    else:
        mimeText = MIMEText(content, 'plain', 'utf-8')
    try:
        # 带有附件
        if attachFile:
            msg = MIMEMultipart()
            msg.attach(mimeText)
            if isinstance(attachFile, list):
                for file in attachFile:
                    if not os.path.exists(file) or not os.path.isfile(file):
                        continue
                    with open(file, 'rb') as f:
                        mime = MIMEBase('file', os.path.splitext(file)[-1][1:], filename=file)
                        mime.add_header('Content-Disposition', 'attachment', filename=os.path.split(file)[1])
                        mime.add_header('Content-ID', '<0>')
                        mime.add_header('X-Attachment-Id', '0')
                        mime.set_payload(f.read())
                        encoders.encode_base64(mime)
                        msg.attach(mime)
            elif os.path.exists(attachFile) and os.path.isfile(attachFile):
                # 添加附件就是加上一个MIMEBase，从本地读取一个图片:
                with open(attachFile, 'rb') as f:
                    mime = MIMEBase('file', os.path.splitext(attachFile)[-1][1:], filename=attachFile)
                    mime.add_header('Content-Disposition', 'attachment', filename=os.path.split(attachFile)[1])
                    mime.add_header('Content-ID', '<0>')
                    mime.add_header('X-Attachment-Id', '0')
                    mime.set_payload(f.read())
                    encoders.encode_base64(mime)
                    msg.attach(mime)
            else:
                raise Exception("附件不存在！！")
        else:
            msg = mimeText

        msg['From'] = fromAccount
        msg['Subject'] = Header(subject, 'utf-8').encode()

        # 补充一个 DATE 的字段 @http://121.33.214.30:28888/pro/task-view-236.html
        # now = datetime.datetime.now()
        # formatted_time = now.strftime('%a, %d %b %Y %H:%M:%S +0800')
        # msg['Date'] = formatted_time
        
        if isinstance(to, list):
            msg['To'] = ','.join(to)
        else:
            msg['To'] = to
        if cc:
            if isinstance(cc, str):
                cc = cc.split(';')
            msg['Cc'] = ','.join(cc)
        if bcc:
            if isinstance(bcc, list):
                msg['Bcc'] = ','.join(bcc)
            else:
                msg['Bcc'] = bcc

        if isSSL:
            sev = smtplib.SMTP_SSL(server1, port)
        else:
            sev = smtplib.SMTP(server1, port)
        # sev.set_debuglevel(1)
        sev.login(account, passwd)
        if isinstance(to, list):
            _to = msg['To'].split(',')
        else:
            _to = [to]
        if cc:
            _to.extend(cc)
        sev.sendmail(account, _to, msg.as_string())
        suc = True
    except Exception as e:
        logger.error("无法发送邮件")
        logger.error(e)
    finally:
        if sev:
            sev.quit()
    return suc

# @decrypt_params
# @decrypt_helper
def connect(account, passwd, server, protocol='POP3',
            port: int=110, isSSL=False, sslPort: int=995,
            timeout=30000):
    """
    连接邮箱
    :param account: 发送人账号
    :param passwd: 发送人密码
    :param server: 邮件服务器地址
    :param protocol: POP3(最简单)、IMAP(支持文件夹操作)
    :param port: 邮件服务器端口
    :param isSSL: 是否加密
    :param sslPort: 加密端口
    :param timeout: 最长等待时间（毫秒）
    :return: 已连接的邮箱对象
    """
    sev = None
    logger.debug("正在连接邮箱...")
    try:
        if protocol == 'POP3':
            if isSSL:
                sev = NEW_POP3_SSL(server, sslPort)
            else:
                sev = NEW_POP3(server, port)
            sev.set_debuglevel(1)
            sev.user(account)
            sev.pass_(passwd)
        if protocol == 'IMAP':
            if isSSL:
                sev = imaplib.IMAP4_SSL(host=server, port=sslPort)
            else:
                sev = imaplib.IMAP4(host=server, port=port)
            sev.login(account, passwd)
    except Exception as e:
        logger.error("无法连接邮箱")
        logger.error(e)
    return sev


def disconnect(sev=None):
    """
    关闭邮箱连接
    :param sev: 已连接的邮箱对象
    :return: 是否关闭成功
    """
    suc = False
    logger.debug("正在关闭邮箱连接...")
    try:
        if sev and isinstance(sev, poplib.POP3):
            sev.quit()
            suc = True
        if sev and isinstance(sev, imaplib.IMAP4):
            sev.logout()
            suc = True
    except Exception as e:
        logger.error("无法关闭邮箱连接")
        logger.error(e)
    return suc


def __getMailByIMAP(sev, index):
    """
    获取指定序号邮件(IMAP协议)
    :param sev: 已连接的邮箱对象
    :param index: 指定序号，从1开始
    :return: 解码后的邮件对象
    """
    msg = None
    logger.debug("正在获取指定序号邮件(IMAP协议)...")
    try:
        sev.select('INBOX', readonly=True)
        # 全部邮件
        _status, _data = sev.search(None, 'ALL')
        msgList = _data[0].split()
        # 取最后一封
        last = msgList[len(msgList) - index]
        _status, _datas = sev.fetch(last, '(RFC822)')
        # 解析出邮件
        msg = email.message_from_bytes(_datas[0][1])
    except Exception as e:
        logger.error("无法获取指定序号邮件(IMAP协议)")
        logger.error(e)
    return msg


def __getMailByPOP3(sev, index):
    """
    获取指定序号邮件(POP3协议)
    :param sev: 已连接的邮箱对象
    :param index: 指定序号，从1开始
    :return: 邮件标题
    """
    msg = None
    logger.debug("正在获取指定序号邮件(POP3协议)...")
    try:
        # stat()返回邮件数量和占用空间:
        # print('Messages: %s. Size: %s' % sev.stat())
        # list()返回所有邮件的编号:
        resp, mails, octets = sev.list()
        # 可以查看返回的列表类似[b'1 82923', b'2 2184', ...]
        # print(mails)
        size = len(mails)
        resp, lines, octets = sev.retr(size - index)
        # lines存储了邮件的原始文本的每一行,
        # 可以获得整个邮件的原始文本:
        msg_content = b'\r\n'.join(lines).decode('utf-8')
        msg = Parser().parsestr(msg_content)

        # index = len(mails)
        # for i in range(index):
        #     resp, lines, octets = sev.retr(i + 1)
        #     # lines存储了邮件的原始文本的每一行,
        #     # 可以获得整个邮件的原始文本:
        #     msg_content = b'\r\n'.join(lines).decode('utf-8')
        #     # 解析出邮件
        #     msg = Parser().parsestr(msg_content)
        #     subject = EmailDecoder.getSubject(msg)
    except Exception as e:
        logger.error("无法获取指定序号邮件(POP3协议)")
        logger.error(e)
    return msg


def readSubject(sev, index,
                timeout=30000):
    """
    获取指定序号邮件的标题
    :param sev: 已连接的邮箱对象
    :param index: 指定序号，从1开始
    :return: 邮件标题
    """
    if sev and isinstance(sev, poplib.POP3):
        return __readSubjectByPOP3(sev, index)
    if sev and isinstance(sev, imaplib.IMAP4):
        return __readSubjectByIMAP(sev, index)
    return None


def __readSubjectByIMAP(sev, index):
    """
    获取指定序号邮件的标题(IMAP协议)
    :param sev: 已连接的邮箱对象
    :param index: 指定序号，从1开始
    :return: 邮件标题
    """
    subject = None
    logger.debug("正在获取指定序号邮件的标题(IMAP协议)...")
    try:
        msg = __getMailByIMAP(sev, index)
        subject = EmailDecoder.getSubject(msg)
    except Exception as e:
        logger.error("无法获取指定序号邮件的标题(IMAP协议)")
        logger.error(e)
    return subject


def __readSubjectByPOP3(sev, index):
    """
    获取指定序号邮件的标题(POP3协议)
    :param sev: 已连接的邮箱对象
    :param index: 指定序号，从1开始
    :return: 邮件标题
    """
    subject = None
    logger.debug("正在获取指定序号邮件的标题(POP3协议)...")
    try:
        msg = __getMailByPOP3(sev, index)
        subject = EmailDecoder.getSubject(msg)
    except Exception as e:
        logger.error("无法获取指定序号邮件的标题(POP3协议)")
        logger.error(e)
    return subject


def readFrom(sev, index,
             timeout=30000):
    """
    获取指定序号邮件的发件人
    :param sev: 已连接的邮箱对象
    :param index: 指定序号，从1开始
    :return: 邮件发件人
    """
    if sev and isinstance(sev, poplib.POP3):
        return __readFromByPOP3(sev, index)
    if sev and isinstance(sev, imaplib.IMAP4):
        pass
    return None


def __readFromByPOP3(sev, index):
    """
    获取指定序号邮件的发件人(POP3协议)
    :param sev: 已连接的邮箱对象
    :param index: 指定序号，从1开始
    :return: 邮件发件人
    """
    _from = None
    logger.debug("正在获取指定序号邮件的发件人(POP3协议)...")
    try:
        msg = __getMailByPOP3(sev, index)
        _from = EmailDecoder.getFrom(msg)
    except Exception as e:
        logger.error("无法获取指定序号邮件的发件人(POP3协议)")
        logger.error(e)
    return _from


def readTo(sev, index,
           timeout=30000):
    """
    获取指定序号邮件的收件人列表
    :param sev: 已连接的邮箱对象
    :param index: 指定序号，从1开始
    :return: 邮件收件人列表
    """
    if sev and isinstance(sev, poplib.POP3):
        return __readToByPOP3(sev, index)
    if sev and isinstance(sev, imaplib.IMAP4):
        pass
    return None


def __readToByPOP3(sev, index):
    """
    获取指定序号邮件的收件人列表(POP3协议)
    :param sev: 已连接的邮箱对象
    :param index: 指定序号，从1开始
    :return: 邮件收件人列表
    """
    to = None
    logger.debug("正在获取指定序号邮件的收件人列表(POP3协议)...")
    try:
        msg = __getMailByPOP3(sev, index)
        to = EmailDecoder.getTo(msg)
    except Exception as e:
        logger.error("无法获取指定序号邮件的收件人列表(POP3协议)")
        logger.error(e)
    return to


def readDate(sev, index,
             timeout=30000):
    """
    获取指定序号邮件的发送日期
    :param sev: 已连接的邮箱对象
    :param index: 指定序号，从1开始
    :return: 邮件发送日期
    """
    if sev and isinstance(sev, poplib.POP3):
        return __readDateByPOP3(sev, index)
    if sev and isinstance(sev, imaplib.IMAP4):
        pass
    return None


def __readDateByPOP3(sev, index):
    """
    获取指定序号邮件的发送日期(POP3协议)
    :param sev: 已连接的邮箱对象
    :param index: 指定序号，从1开始
    :return: 邮件发送日期
    """
    _date = None
    logger.debug("正在获取指定序号邮件的发送日期(POP3协议)...")
    try:
        msg = __getMailByPOP3(sev, index)
        _date = EmailDecoder.getDate(msg)
    except Exception as e:
        logger.error("无法获取指定序号邮件的发送日期(POP3协议)")
        logger.error(e)
    return _date


def readContent(sev, index,
                timeout=30000):
    """
    获取指定序号邮件的正文
    :param sev: 已连接的邮箱对象
    :param index: 指定序号，从1开始
    :return: 邮件正文
    """
    if sev and isinstance(sev, poplib.POP3):
        return __readContentByPOP3(sev, index)
    if sev and isinstance(sev, imaplib.IMAP4):
        pass
    return None


def __readContentByPOP3(sev, index):
    """
    获取指定序号邮件的正文(POP3协议)
    :param sev: 已连接的邮箱对象
    :param index: 指定序号，从1开始
    :return: 邮件正文
    """
    content = None
    logger.debug("正在获取指定序号邮件的正文(POP3协议)...")
    try:
        msg = __getMailByPOP3(sev, index)
        content = EmailDecoder.getContent(msg)
    except Exception as e:
        logger.error("无法获取指定序号邮件的正文(POP3协议)")
        logger.error(e)
    return content


def downloadAttach(sev, index, filePath,
                   timeout=30000):
    """
    获取指定序号邮件的附件列表
    :param sev: 已连接的邮箱对象
    :param index: 指定序号，从1开始
    :param filePath: 附件下载路径
    :return: 邮件附件名列表
    """
    if not filePath.endswith(os.sep):
        filePath += os.sep
    if not os.path.exists(filePath):
        os.makedirs(filePath)
    if sev and isinstance(sev, poplib.POP3):
        return __readAttachByPOP3(sev, index, filePath)
    if sev and isinstance(sev, imaplib.IMAP4):
        pass
    return None


def __readAttachByPOP3(sev, index, filePath):
    """
    获取指定序号邮件的附件列表(POP3协议)
    :param sev: 已连接的邮箱对象
    :param index: 指定序号，从1开始
    :param filePath: 附件下载路径
    :return: 邮件附件名列表
    """
    attach = None
    logger.debug("正在获取指定序号邮件的附件名列表(POP3协议)...")
    try:
        msg = __getMailByPOP3(sev, index)
        attach = EmailDecoder.getAttach(msg, filePath)
    except Exception as e:
        logger.error("无法获取指定序号邮件的附件名列表(POP3协议)")
        logger.error(e)
    return attach


def getAllMail(sev):
    """
    获取近一个月的邮件列表
    :param sev: 已连接的邮箱对象
    :return:
    """
    mailList = []
    logger.debug("正在通过POP3协议获取邮件列表...")
    try:
        resp, mails, octets = sev.list()
        # 可以查看返回的列表类似[b'1 82923', b'2 2184', ...]
        size = len(mails)
        for i in range(size):
            resp, lines, octets = sev.retr(size - i)
            # lines存储了邮件的原始文本的每一行,
            # 可以获得整个邮件的原始文本:
            msg_content = b'\r\n'.join(lines).decode('utf-8', errors='ignore')
            # 解析出邮件
            msg = Parser().parsestr(msg_content)
            subject = EmailDecoder.getSubject(msg)
            _from = EmailDecoder.getFrom(msg)
            to = EmailDecoder.getTo(msg)
            _date = EmailDecoder.getDate(msg)
            # print('标题：%s --- 发件人：%s --- 收件人：%s --- 发送日期：%s' % (subject, _from, to, _date))

            mailList.append({
                '邮件序号': i,
                '邮件标题': subject,
                '发送日期': _date
            })
        return mailList
    except Exception as e:
        logger.error("获取邮件列表失败！")
        logger.error(e)
