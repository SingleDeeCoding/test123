import collections
import inspect
import json
import logging
import os
import re
import sys
import traceback

DEFAULT_FORMAT = '%(message)s' if os.environ.get("ENTITY",None) == "studio" else '[%(levelname)s] %(asctime)s  %(filename)s  [line:%(lineno)d] %(message)s'
logging.basicConfig(level=logging.WARNING,
                    # format='[%(levelname)s] %(asctime)s [line:%(lineno)d] %(message)s', datefmt='%m-%d %H:%M:%S')  # 缩减版
                    format=DEFAULT_FORMAT,
                    datefmt='%m-%d %H:%M:%S')  # 缩减版


# format='[%(levelname)s] %(asctime)s %(filename)s [line:%(lineno)d] %(funcName)s %(message)s')
class ComponentLogger(logging.Logger):
    ## 组件的日志输出 每次都在日志面加上 [流程ID][组件ID]
    # flag="component.v1"
    _error_dictionary = None

    def __init__(self, name, level=logging.NOTSET):
        self.parent = logging.root
        # level = os.environ.get("LOGLEVEL", level)
        super().__init__(name=name, level=level)
        if not self._error_dictionary:
            dic_path = os.path.join(os.path.dirname(__file__), "Exception_translate.json")
            if os.path.exists(dic_path):
                with open(dic_path, mode="r", encoding="utf-8") as f:
                    self._error_dictionary = json.load(f)
                    
    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, flow_id=None, node_id=None):
        "流程中直接调用该 logger 时,会传入当前的流程id和节点id"
        from sendiRPA import GlobalStatus, id_generator
        stacks = inspect.stack()
        os.environ["IGNORE_FILE"] = "0"
        # print(">>>>>>",flow_id_from_error_info,node_id_from_error_info,"<<<<<")
        # print(os.environ.get("CURRENT_FILE"))
        # print(stacks)
        # print(f"{self.name}{msg}")
        try:
            # 机器人运行状态下,保持原来的输出
            if os.environ.get("ENTITY", None) != "studio"  and os.environ.get("MODE", "run") == "run":
                return super()._log(level, msg, args, exc_info=exc_info, extra=extra, stack_info=stack_info)

            # 只处理流程易的输出，过滤掉第三方库的输出 。机器人运行状态下,保持原来的输出
            if not self.name.startswith("component.v1") and not self.name.startswith("systemerror.v1"):
                # print(f"{self.name,exc_info,extra,stack_info,self}")
                return super()._log(level, msg, args, exc_info=exc_info, extra=extra, stack_info=stack_info)

            # 自定义代码的情况下,如果传了flow_id,node_id，也必须改为自定义代码块节点的flow id和node id
            if os.environ.get("IS_CUSTOM_CODE", "0") == "1":
                flow_id,node_id = GlobalStatus.current_flow_id,GlobalStatus.current_node_id

            # 处理下msg的参数.跟logging源码的逻辑一致
            if (args and len(args) == 1 and isinstance(args[0], collections.abc.Mapping)
                    and args[0]):
                args = args[0]
            if args:
                # print(msg,args)
                msg = msg % args

            # 处理下转义字符 %
            if isinstance(msg,str):
                msg = msg.replace("%","%%")
            else:
                try:
                    msg = json.dumps(msg,ensure_ascii=False)
                    msg  = msg.replace("%","%%")
                    msg = json.loads(msg)
                except:
                    pass
        
            msg_list = self._splice_content(content=msg,max_length=int(os.environ.get("MAX_LOG_LENGTH", 10000)) or 10000)
            for index, msg in enumerate(msg_list):
                if os.environ.get("IS_CUSTOM_COMPONENT", '0') == "1":
                    ## 当前输出属于自定义组件,则自定义组件里面的输出都属于该组件
                    _, file_name = os.path.split(os.environ.get("CURRENT_FILE"))
                    ## 调试模式下,行数什么的放在 debug 程序做
                    if os.environ.get("MODE", "run") == "debug":
                        fmt = json.dumps({
                            "id": id_generator.get(),
                            "flowid": os.environ["CUSTOM_FLOW_ID"],
                            "logType": "%(levelname)s",
                            "nodeid": os.environ["CUSTOM_NODE_ID"],
                            # message不能再dump后再去替换，否则会出现转义的问题,必须在dump之前
                            "message": f"%(asctime)s [todo.py] [line:todo]{msg}" if index == 0 else msg,
                            "codeLine": os.environ.get('CUSTOM_CONPOMENT_LINE_NUMBER', 0),
                            "originLogFile": os.environ.get("LOGPATH", None),
                            "subContent": False if index == 0 else True,
                            "file_path":os.environ.get("CURRENT_FILE")
                        }, ensure_ascii=False)
                    else:
                        fmt = json.dumps({
                            "id": id_generator.get(),
                            "flowid": os.environ["CUSTOM_FLOW_ID"],
                            "logType": "%(levelname)s",
                            "nodeid": os.environ["CUSTOM_NODE_ID"],
                            # message不能再dump后再去替换，否则会出现转义的问题,必须在dump之前
                            "message": f"%(asctime)s {file_name} [line:{os.environ.get('CUSTOM_CONPOMENT_LINE_NUMBER', 0)}] {msg}" if index == 0 else msg,
                            # "message": msg,
                            "codeLine": os.environ.get('CUSTOM_CONPOMENT_LINE_NUMBER', 0),
                            "originLogFile": os.environ.get("LOGPATH", None),
                            "subContent": False if index == 0 else True,
                            "file_path":os.environ.get("CURRENT_FILE")
                        }, ensure_ascii=False)
                    GlobalStatus.current_node_line_number = os.environ.get('CUSTOM_CONPOMENT_LINE_NUMBER', 0)
                elif self.name == "systemerror.v1":
                    ## 当前输出属于主流程的catch
                    # print(f">>>>>{os.environ.get('ERROR_SCRIPT_PATH',None),os.environ.get('CURRENT_FILE')}")
                    fmt = json.dumps({
                        "id": id_generator.get(),
                        "flowid": flow_id or GlobalStatus.current_flow_id,
                        "logType": "%(levelname)s",
                        "nodeid": node_id or GlobalStatus.current_node_id,
                        "message": f"%(asctime)s tmp.py [line:{GlobalStatus.current_node_line_number}] {msg}" if index == 0 else msg,
                        # "message": msg,
                        "codeLine": GlobalStatus.current_node_line_number,
                        "originLogFile": os.environ.get("LOGPATH", None),
                        "subContent": False if index == 0 else True,
                        "file_path":  os.environ.get("CURRENT_FILE")

                    }, ensure_ascii=False)
                    # GlobalStatus.current_node_line_number = stack.lineno
                else:
                    _, file_name = os.path.split(os.environ.get("CURRENT_FILE"))
                    # print(stacks)
                    # print(file_name)
                    # print(os.environ.get("MODE"))
                    for stack in stacks:
                        if (stack.function == "<module>" and os.environ.get("MODE", "run") == "debug"):
                            # 调试,调试直接返回 ，正确的行数替换/文件名在debug程序里面做
                            fmt = json.dumps({
                                "id": id_generator.get(),
                                "flowid": flow_id or GlobalStatus.current_flow_id,
                                "logType": "%(levelname)s",
                                "nodeid": node_id or GlobalStatus.current_node_id,
                                "message": f"%(asctime)s [todo.py] [line:todo]{msg}" if index == 0 else msg,
                                "codeLine": stack.lineno,
                                "originLogFile": os.environ.get("LOGPATH", None),
                                "subContent": False if index == 0 else True,
                                "file_path": os.environ.get("CURRENT_FILE")
                            }, ensure_ascii=False)
                            GlobalStatus.current_node_line_number = stack.lineno
                            break
                        elif stack.filename == os.environ.get("CURRENT_FILE"):
                            _, file_name = os.path.split(stack.filename)
                            fmt = json.dumps({
                                "id": id_generator.get(),
                                "flowid": flow_id or GlobalStatus.current_flow_id,
                                "logType": "%(levelname)s",
                                "nodeid": node_id or GlobalStatus.current_node_id,
                                "message": f"%(asctime)s {file_name} [line:{stack.lineno}]{msg}" if index == 0 else msg,
                                # "message": msg,
                                "codeLine": stack.lineno,
                                "originLogFile": os.environ.get("LOGPATH", None),
                                "subContent": False if index == 0 else True,
                                "file_path": os.environ.get("CURRENT_FILE")
                            }, ensure_ascii=False)
                            GlobalStatus.current_node_line_number = stack.lineno
                            break
                    else:
                        fmt = json.dumps({
                            "id": id_generator.get(),
                            "flowid": flow_id or GlobalStatus.current_flow_id,
                            "logType": "%(levelname)s",
                            "nodeid": node_id or GlobalStatus.current_node_id,
                            "message": f"%(asctime)s {file_name} [line:{GlobalStatus.current_node_line_number}]{msg}" if index == 0 else msg,
                            # "message": msg,
                            "codeLine": GlobalStatus.current_node_line_number,
                            "originLogFile": os.environ.get("LOGPATH", None),
                            "subContent": False if index == 0 else True,
                            "file_path": os.environ.get("CURRENT_FILE")
                        }, ensure_ascii=False)

                new_fmt = logging.Formatter(
                    # f'[{flow_id or GlobalStatus.current_flow_id}] [{node_id or GlobalStatus.current_node_id}] [%(levelname)s] %(asctime)s {file_name} [line:{stack.lineno}] %(message)s',
                    fmt=fmt,
                    datefmt='%m-%d %H:%M:%S')
                logging.root.handlers[0].setFormatter(new_fmt)
                super()._log(level, msg, (), exc_info=exc_info, extra=extra, stack_info=stack_info)
                # sys.stderr.flush()
        except:
            raise
        finally:
            os.environ["IGNORE_FILE"] = "1"
            logging.root.handlers[0].setFormatter(logging.Formatter(
                fmt=DEFAULT_FORMAT,
                datefmt='%m-%d %H:%M:%S'
            )) # 恢复默认的format

    def _splice_content(self, content, max_length=None):
        # max_length = max_length or os.environ.get("MAX_LOG_LENGTH") or 10000
        max_length = max(max_length - 100, 100)  # 减去日志消息头
        if not isinstance(content, str):
            content = str(content)
        if len(content) >= max_length:
            res = list()
            parts = len(content) // max_length
            for i in range(parts):
                res.append(content[i * max_length:i * max_length + max_length])
            if len(content) % max_length != 0:
                res.append(content[parts * max_length:len(content)])
            return res
        else:
            return [content]

    def info(self, msg, *args, **kwargs):
        msg,args,kwargs = self.en2cn(msg, *args, **kwargs)

        return super().info(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        msg,args,kwargs = self.en2cn(msg, *args, **kwargs)

        return super().error(msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        msg,args,kwargs = self.en2cn(msg, *args, **kwargs)

        return super().warn(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        msg,args,kwargs = self.en2cn(msg, *args, **kwargs)

        return super().warning(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        msg,args,kwargs = self.en2cn(msg, *args, **kwargs)

        return super().debug(msg, *args, **kwargs)

    def get_ids_from_error_info(self, err_info:str):
        from sendiRPA import GlobalStatus
        node_id, error_node_line_number =  None, 0
        try:
            # 匹配报错节点的行数
            pat = "line ([0-9]*)"
            error_node_line_number = re.findall(pat, err_info)[-1] #最下一行即为对应的
            # 匹配报错的文件
            self.get_error_file_path(err_info)
            if os.environ.get("RAISE_BY_CUSTOM_CODE","0") == "0": #自定义代码抛出的错误，以自定义代码块的flowId,nodeId为准
                pat = r"flow_id='"+GlobalStatus.current_flow_id+"', node_id=\'([A-Za-z0-9]*)\'"
                # print("pat -> ",pat)
                node_id = re.findall(pat, err_info)[-1]  # 匹配报错的节点
            else:
                pass
        except:
            return  node_id,error_node_line_number
        finally:
            return node_id, error_node_line_number


    def get_error_file_path(self,err_info):
        # 获取下报错的文件
        try:
            err_info_list = err_info.split(" File ")
            pat = "\"([\S\s]*)\","
            os.environ["CURRENT_FILE"] = re.findall(pat, err_info_list[-1])[-1]
        except:
            pass


    def en2cn(self,msg, *args, **kwargs):
        ## 错误信息中文化  TODO 继承 SystemErrorLogger?
        if self._error_dictionary:
            _type, _value, _traceback=  sys.exc_info()
            if not _type:
                return msg,args,kwargs
            custom_errs = self._error_dictionary.get(_type.__name__, None)
            if not custom_errs:
                return msg,args,kwargs
            ## 英文转中文
            for custom_err in custom_errs:
                match = re.search(custom_err["regex"], str(_value))
                if match:
                    params = {f'{custom_err["param"][i]}': match.group(i + 1) for i in
                              range(len(custom_err['param']))}
                    cn_value = custom_err["chinese_error"].format(**params)
                    msg = cn_value
                    if "exc_info" in kwargs:
                        kwargs["exc_info"] = (_type, _type(cn_value), _traceback)
                        # kwargs.pop("exc_info")
                    # return super().error(msg, *args, exc_info=(_type, _type(cn_value), _traceback), **kwargs)
                return msg,args,kwargs

class RobotLogger(logging.Logger):

    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name=name, level=level)

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, **kwargs):
        for stack in inspect.stack():
            if stack.filename == os.environ.get("CURRENT_FILE"):
                _, file_name = os.path.split(stack.filename)
                fmt =  f'[%(levelname)s] %(asctime)s {file_name}  [line:{stack.lineno}] %(message)s'
                new_fmt = logging.Formatter(
                    fmt=fmt,
                    datefmt='%m-%d %H:%M:%S')
                logging.root.handlers[0].setFormatter(new_fmt)
                break
        return super()._log(level, msg, args, exc_info=exc_info, extra=extra, stack_info=stack_info)

if os.environ.get("ENTITY",None) == "studio" or os.environ.get("MODE", "run") == "debug":
    logger = ComponentLogger(name="component.v1", level=logging.DEBUG)
    logger.parent = logging.root  # 按照一开始的设计用的 root stream handler
else:
    # logging.getLogger().setLevel(logging.ERROR)
    logger = RobotLogger(name="root.c1",level=logging.DEBUG)
    logger.parent = logging.root  # 按照一开始的设计用的 root stream handler
    logger.setLevel(logging.DEBUG)

log_level = os.environ.get("LOGLEVEL", "DEBUG")
logger.setLevel(log_level.upper())
if os.environ.get("FLOWSTATE", "") == "":
    # print(f"{'*' * 20} 当前运行日志等级:{log_level} {'*' * 20}")
    os.environ.setdefault("FLOWSTATE", "RUNNING")

logging.Logger.manager.loggerDict.update({
    "component.v1": logger
})



if os.environ.get("ENTITY", None) == "studio":
    logging.Logger.manager.loggerClass = ComponentLogger

# def setup():
#     # 第一次运行
#     if GlobalStatus.entry_flow_script is None:
#         GlobalStatus.entry_flow_script = os.environ.get("CURRENT_FILE")
#         GlobalStatus.subflow_line_number_inc = len(global_v.keys())



# print(logging.Logger.manager.loggerDict)


class SystemErrorLogger(ComponentLogger):
    _error_dictionary = None

    def __init__(self, name, level):
        if not self._error_dictionary:
            dic_path = os.path.join(os.path.dirname(__file__), "Exception_translate.json")
            if os.path.exists(dic_path):
                with open(dic_path, mode="r", encoding="utf-8") as f:
                    self._error_dictionary = json.load(f)

        super().__init__(name, level)

    def error(self, msg, *args, **kwargs) -> None:
        from sendiRPA import GlobalStatus
        GlobalStatus.current_node_id, GlobalStatus.current_node_line_number \
            = self.get_ids_from_error_info(
        err_info=traceback.format_exc())
        # print(f" ->  {GlobalStatus.current_node_id, GlobalStatus.current_node_line_number}")
        if self._error_dictionary:
            _type, _value, _traceback = sys.exc_info()
            if not _type:
                return super().error(msg, *args, **kwargs)
            custom_errs = self._error_dictionary.get(_type.__name__, None)
            if not custom_errs:
                return super().error(msg, *args, **kwargs)
            ## 英文转中文
            for custom_err in custom_errs:
                match = re.search(custom_err["regex"], str(_value))
                if match:
                    params = {f'{custom_err["param"][i]}': match.group(i + 1) for i in
                              range(len(custom_err['param']))}
                    cn_value = custom_err["chinese_error"].format(**params)
                    if "exc_info" in kwargs:
                        kwargs.pop("exc_info")
                    return super().error(msg, *args, exc_info=(_type, _type(cn_value), _traceback), **kwargs)
        return super().error(msg, *args, **kwargs)

    def handle(self, record) -> None:
        return super().handle(record)


systemError = SystemErrorLogger(name="systemerror.v1", level=logging.ERROR)
systemError.parent = logging.root