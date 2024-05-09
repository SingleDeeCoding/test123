import uuid

from logHandler import logger
import shutil
import os,sys
# import PVC
import threading
import time
# import ScreenRecorder
# import BrowserRecoder
import subprocess
import platform
import zipfile
import traceback
import base64
from Decorator import protocolRaise
# from RobotException import RobotException
# from screen_recorder import ScreenRecord

def copy(srcPath, dstPath, overwrite=False):
    """
    复制文件或文件夹
    :param srcPath: 源文件路径
    :param dstPath: 目标文件路径
    :param overwrite: 是否覆盖
    :return: 是否复制成功
    """
    suc = False
    if srcPath == dstPath:
        logger.error("源文件/文件夹路径与目标文件/文件夹路径不能相同！")
        return suc
    if not os.path.exists(srcPath):
        logger.error("源文件/文件夹不存在！")
        return suc
    if overwrite is False and os.path.exists(dstPath):
        logger.error("目标文件/文件夹已存在，且不覆盖！")
        return suc
    if overwrite and os.path.exists(dstPath):
        shutil.rmtree(dstPath) if os.path.isdir(dstPath) else os.remove(dstPath)
    try:
        if os.path.isfile(srcPath):
            logger.debug("正在复制文件...")
            shutil.copy2(srcPath, dstPath)
            suc = True
        else:
            assert os.path.isdir(srcPath), f"源数据路径{srcPath}不是一个合法的文件夹路径"
            logger.debug("正在复制文件夹...")
            shutil.copytree(srcPath, dstPath)
            suc = True
    except Exception as e:
        logger.error("无法复制文件")
        logger.error(e)
    return suc


def move(srcPath, dstPath, overwrite=False):
    """
    移动文件或文件夹
    :param srcPath: 源文件路径
    :param dstPath: 目标文件路径
    :param overwrite: 是否覆盖
    :return: 是否移动成功
    """
    suc = False
    logger.debug("正在移动文件...")
    if srcPath == dstPath:
        logger.error("源文件路径与目标文件路径不能相同！")
        return suc
    if not os.path.exists(srcPath):
        logger.error("源文件不存在！")
        return suc
    if overwrite is False and os.path.exists(dstPath):
        logger.error("目标文件已存在，且不覆盖！")
        return suc
    try:
        shutil.move(srcPath, dstPath)
        suc = True
    except Exception as e:
        logger.error("无法移动文件")
        logger.error(e)
    return suc


def rename(srcPath, dstPath, overwrite=False):
    """
    重命名文件或文件夹
    :param srcPath: 源文件路径
    :param dstPath: 目标文件路径
    :param overwrite: 是否覆盖
    :return: 是否重命名成功
    """
    suc = False
    logger.debug("正在重命名文件...")
    if srcPath == dstPath:
        logger.error("源文件路径与目标文件路径不能相同！")
        return suc
    if not os.path.exists(srcPath):
        logger.error("源文件不存在！")
        return suc
    if overwrite is False and os.path.exists(dstPath):
        logger.error("目标文件已存在，且不覆盖！")
        return suc
    try:
        shutil.move(srcPath, dstPath)
        suc = True
    except Exception as e:
        logger.error("无法重命名文件")
        logger.error(e)
    return suc


def delete(srcPath=''):
    """
    删除文件或文件夹
    :param srcPath: 源文件路径
    :return: 是否删除成功
    """
    suc = False
    try:
        if os.path.isfile(srcPath):
            logger.debug("正在删除文件...")
            if not os.path.exists(srcPath):
                logger.error("源文件不存在！")
                return suc
            else:

                os.remove(srcPath)
                suc = True
        else:
            logger.debug(f"正在删除文件夹:{srcPath}...")
            assert os.path.isdir(srcPath), f"目标路径{srcPath}不是一个合法的文件夹路径"
            shutil.rmtree(srcPath)
            suc = True
    except Exception as e:
        logger.error("无法删除文件")
        logger.error(e)
        suc = False
    finally:
        return suc


def getDownloadPath():
    """
    获取默认下载路径
    :return: 路径
    """
    path = None
    logger.debug("正在获取默认下载路径...")
    try:
        path = os.path.join(os.path.expanduser('~'), 'Downloads')
    except Exception as e:
        logger.error("无法获取默认下载路径")
        logger.error(e)
    return path


def mkdir(srcPath=''):
    """
    创建文件夹
    :param srcPath: 文件夹路径
    :return: 是否创建成功
    """
    suc = False
    logger.debug("正在创建文件夹...")
    try:
        isExists = os.path.exists(srcPath)
        if isExists:
            logger.warning('文件夹已存在，无需创建')
            return suc
        os.makedirs(srcPath)
        suc = True
    except Exception as e:
        logger.error("无法创建文件夹")
        logger.error(e)
    return suc


def exists(srcPath=''):
    """
    判断文件或文件夹是否存在
    :param srcPath: 文件或文件夹路径
    :return: 是否存在
    """
    suc = False
    logger.debug("正在判断文件或文件夹是否存在...")
    try:
        if not os.path.isfile(srcPath) and not os.path.isdir(srcPath):
            logger.warning("检测到\"路径\"参数不是文件路径或文件夹路径！")
            return suc
        suc = os.path.exists(srcPath)
    except Exception as e:
        logger.error("无法判断文件或文件夹是否存在")
        logger.error(e)
    return suc


def getFiles(srcPath, orderField, reverse=False):
    """
    获取文件列表，支持排序
    :param srcPath: 文件夹路径
    :param orderField: 排序属性：文件大小、文件名、创建日期、修改日期
    :param reverse: 是否要降序排序；降序:True，升序:False（默认）
    :return: 文件列表
    """
    fileList = None
    logger.debug("正在获取文件列表...")
    try:
        if os.path.isfile(srcPath):
            return srcPath
        fileList = os.listdir(srcPath)
        if fileList is None:
            return fileList
        fileList = list(map(lambda x: os.path.join(srcPath, x), fileList))
        if orderField == '创建日期':
            fileList.sort(key=lambda x: os.stat(x).st_ctime, reverse=reverse)
        if orderField == '文件大小':
            fileList.sort(key=lambda x: os.path.getsize(x), reverse=reverse)
        if orderField == '修改日期':
            fileList.sort(key=lambda x: os.stat(x).st_mtime, reverse=reverse)
        if orderField == '文件名':
            fileList.sort(key=lambda x: os.path.basename(x), reverse=reverse)
    except Exception as e:
        logger.error("无法获取文件列表")
        logger.error(e)
    return fileList


def getFileName(srcPath, extension=False):
    """
    获取文件名
    :param srcPath: 源文件路径
    :param extension: 是否包含扩展名
    :return: 路径中的文件名
    """
    fileName = None
    logger.debug("正在获取文件名...")
    try:
        if os.path.isdir(srcPath):
            logger.error('源文件路径是个文件夹，没有文件名')
            return fileName
        if extension:
            fileName = os.path.basename(srcPath)
        else:
            fileName = os.path.split(srcPath)[1]
            fileName = os.path.splitext(fileName)[0]
    except Exception as e:
        logger.error("无法获取文件名")
        logger.error(e)
    return fileName


def __getModule():
    return 'task'


def __getBaseRequest(module, method, data=None):
    baseRequest = {
        'module': module,
        'method': method,
        'data': data
    }
    return baseRequest


@protocolRaise(def_return=None)
def upload(srcPath='', continue_on_400=False):
    """
    文件上传
    todo 校验文件类型、大小
    :param srcPath: 源文件路径
    :param continue_on_400: 通信出错是否继续
    :return: 服务器返回的文件下载URL
    """
    url = None
    if not srcPath or not os.path.exists(srcPath):
        logger.error('无法上传文件，源文件不存在！')
        return url
    try:
        url = PVC._uploadFile(localPath=srcPath, method='uploadFile', _type='uploadFileUrl',
                              continue_on_400=continue_on_400)
    except RobotException as e:
        logger.error("无法上传文件，请先登录机器人")
        url = 'robot'
    except Exception as e:
        logger.error("无法上传文件")
        logger.debug(e)
    return url


def download(url, dstPath):
    """
    文件下载
    todo 是否覆盖
    :param url: 服务器返回的文件下载URL
    :param dstPath: 保存文件的路径
    :return: 是否下载成功
    """
    (filePath, fullName) = os.path.split(url)
    (shotName, extension) = os.path.splitext(fullName)
    uuid = shotName[shotName.index('=') + 1:]
    suc = PVC._downloadFile(uuid=uuid, dstPath=dstPath, method='downloadFile', _type='downloadFile')
    return suc


@protocolRaise(def_return=False)
def uploadPhoto(srcPath='', continue_on_400=False):
    """
    上传任务运行截图
    todo 校验文件类型、大小
    :param srcPath: 截图图片路径
    :param continue_on_400: 通信出错是否继续
    :return: 截图上传是否成功
    """
    suc = False
    if not srcPath or not os.path.exists(srcPath):
        logger.error('无法上传任务运行截图，截图图片不存在！')
        return suc
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    data = {"filePath": srcPath,
            "timestamp": now}
    try:
        uuid = PVC._uploadFile(localPath=srcPath,
                               method='uploadTaskPhoto', _type='uploadTaskPhoto',
                               data=data, continue_on_400=continue_on_400)
        if uuid:
            suc = True
        if uuid == 'console':
            suc = uuid
    except RobotException as e:
        logger.error("无法上传任务运行截图")
        suc = 'robot'
    except Exception as e:
        logger.error("无法上传任务运行截图")
        logger.debug(e)
    return suc


def videoRecordStart(recordType, hWeb=None):
    """
    开始录制视频
    :param recordType: 录制类型：浏览器录屏、全屏录屏
    :param savePath: 录屏保存路径
    :param hWeb: 浏览器对象
    :return: 是否录屏成功
    """
    suc = False
    logger.debug("正在开始录制视频...")
    temp_path = f"{uuid.uuid1()}.mp4"
    try:
        if recordType == 'browser':
            _screen_recorder = ScreenRecord(driver=hWeb,file_name=temp_path)
            _screen_recorder.record_screen()
            # record_thread = threading.Thread(target=BrowserRecoder.record, args=(hWeb, temp_path,))
            # record_thread.start()
            # screenshot_thread = threading.Thread(target=BrowserRecoder.screenshot_to_queue, args=(hWeb,))
            # screenshot_thread.start()
            # suc = True
        elif recordType == 'desktop':
            record_thread = threading.Thread(target=ScreenRecorder.record, args=(temp_path,))
            record_thread.start()
            screenshot_thread = threading.Thread(target=ScreenRecorder.screenshot_to_queue)
            screenshot_thread.start()
            suc = True
    except Exception as e:
        logger.error('无法开始录制视频')
        logger.error(e)
    return suc


@protocolRaise(def_return=False)
def videoRecordStop(isUpload=False, continue_on_400=False, savePath=""):
    """
    结束录制视频
    :param isUpload: 是否同时上传录屏视频
    :param continue_on_400: 通信出错是否继续
    :return: 结束录制视频是否成功
    """
    suc = False
    logger.debug("正在结束录制视频...")
    try:
        srcPath1, startTime1 = ScreenRecorder.stop()
        srcPath2, startTime2 = BrowserRecoder.stop()
        _screen_recorder = ScreenRecord()
        srcPath2 = _screen_recorder.file_name
        _screen_recorder.stop_recording()
        if not srcPath1 and not srcPath2:
            logger.warning('没有开始录制视频，无法结束')
            return suc
        srcPath = srcPath1 if srcPath1 else srcPath2
        startTime = startTime1 if startTime1 else startTime2
        time.sleep(1)
        if isUpload:
            now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            data = {"filePath": srcPath,
                    "startTime": startTime,
                    "endTime": now}
            suc = PVC._uploadFile(localPath=srcPath,
                                  method='uploadTaskVideo', _type='uploadTaskVideo',
                                  data=data, continue_on_400=continue_on_400)
            if suc:
                suc = True
            if suc == 'console':
                suc = suc
        else:
            suc = True
        if os.path.exists(savePath):
            os.remove(savePath)
        shutil.move(srcPath,savePath)
    except RobotException as e:
        logger.error("无法结束录制视频，请先登录机器人")
        suc = 'robot'
    except Exception as e:
        logger.error('无法结束录制视频')
        logger.error(e)
    return suc


def _unzip(srcPath, dstPath, overwrite=False, passwd=None):
    """
    解压缩zip文件
    :param srcPath: 源zip文件
    :param dstPath: 目标目录
    :param overwrite: 是否覆盖
    :param passwd: 密码
    :return: 解压缩zip文件是否成功
    """
    suc = False
    logger.debug("正在解压缩zip文件...")
    try:
        if overwrite and os.path.exists(dstPath):
            shutil.rmtree(dstPath)

        with zipfile.ZipFile(srcPath, 'r') as zpf:
            if passwd:
                zpf.setpassword(passwd.encode('utf-8'))
            # 需要修改zipfile源码避免中文乱码
            # zipfile.py搜索'cp437'，共两处结果
            # 第一个改成filename = filename.decode('gbk')
            # 第二个改成fname_str = fname.decode('gbk')
            zpf.extractall(dstPath)
            # zip_filelist = zpf.namelist()
            # print(zip_filelist)

        # 解压之后需要对于文件做处理
        # wrong_path = None
        # if zip_filelist:
        #     for old_name in zip_filelist:
        #         try:
        #             i = old_name.encode('cp437').decode('gbk')
        #         except:
        #             try:
        #                 i = old_name.encode('cp437').decode('utf-8')
        #             except:
        #                 i = old_name
        #
        #         # 对路径进行转义
        #         old_path = dstPath + os.sep + old_name
        #         old_path = str(old_path).replace("\\", '/')
        #         old_path = str(old_path).replace("\\\\", '/')
        #         new_path = dstPath + os.sep + i
        #         new_path = str(new_path).replace("\\", '/')
        #         new_path = str(new_path).replace("\\\\", '/')
        #         # print('--------------------------')
        #         # print(old_path)
        #         # print("旧流程路径",os.path.exists(old_path))
        #         # print(new_path)
        #         # print("新流程路径", os.path.exists(os.path.dirname(new_path)))
        #         # print('--------------------------')
        #         if old_path != new_path:
        #             if not os.path.isdir(old_path):
        #                 try:
        #                     if os.path.exists(os.path.dirname(new_path)) is False:
        #                         os.makedirs(os.path.dirname(new_path))
        #                         # print('建一个')
        #                     os.rename(old_path, new_path)
        #                 except Exception as e:
        #                     logger.error('出错了', e)
        #             else:
        #                 wrong_path = old_path
        #                 pass
        #     if wrong_path:
        #         shutil.rmtree(wrong_path, ignore_errors=True)
        #
        suc = True
    except RuntimeError as e:
        error_log = str(e.args)
        if 'Bad password' in error_log:
            logger.error('无法解压缩zip文件，密码错误！')
        if 'password required' in error_log:
            logger.error('无法解压缩zip文件，此zip文件已被加密，请填入密码！')
        logger.error("无法解压缩zip文件")
        logger.error(e)
    return suc


# 暂时停用
def _zip(srcPath, dstPath, overwrite=False, passwd=None):
    """
    压缩zip文件
    :param srcPath: 支持传入文件列表
    :param dstPath:
    :param overwrite: 是否覆盖已有zip文件
    :param passwd: 密码
    :return: 压缩zip文件是否成功

    """
    suc = False
    logger.debug("正在压缩zip文件...")
    # zip_exe_path = r'..\Python\python3_lib\Scripts\7z1900-extra\7za.exe'
    # 转为列表方便后续判断
    target_path = srcPath
    if isinstance(srcPath, str):
        target_path = [srcPath]

    if dstPath in target_path:
        logger.error("无法压缩zip文件，源文件路径与目标文件路径不能相同！")
        return suc
    if not all(os.path.exists(t_path) for t_path in target_path):
        logger.error("无法压缩zip文件，源文件不存在！")
        return suc
    if not dstPath.lower().endswith('.zip'):
        logger.error("无法压缩zip文件，目标文件不是zip文件！")
        return suc
    if overwrite is False and os.path.exists(dstPath):
        logger.error("无法压缩zip文件，目标文件已存在，且不覆盖！")
        return suc

    # target_path = " ".join(target_path)
    try:
        import zipfile
        # outputs = ''
        # 必须先移除同名文件，否则会直接在原有压缩文件内添加新文件
        if overwrite and os.path.exists(dstPath):
            os.remove(dstPath)
        with zipfile.ZipFile(dstPath,"w") as z:
            if passwd:
                z.setpassword(passwd.encode("utf-8"))
            for file in target_path:
                if os.path.isdir(file):
                    # dir_list = [file]
                    # while len(dir_list)!=0:
                    for folder_root, _, files in os.walk(file):
                        # print(folder_root, _, files)
                        for file in files:
                            file_path = os.path.join(folder_root, file)
                            _, filename = os.path.split(file)
                            z.write(file_path, filename)
                else:
                    _,filename=os.path.split(file)
                    with open(file,"rb") as f:
                        z.writestr(filename,f.read())
                # z.write(file)
        return True
        # if passwd:
        #     if '"' in passwd:
        #         logger.error('"不能作为密码，加密失败！')
        #         return False
        #
        #     cmd = zip_exe_path + ' a -p{passwd} {dstPath} {srcPath}'.format(dstPath=dstPath,
        #                                                                     srcPath=target_path,
        #                                                                     passwd=passwd)
        # else:
        #     cmd = zip_exe_path + ' a {dstPath} {srcPath}'.format(dstPath=dstPath,
        #                                                          srcPath=target_path)
        # p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1)
        # for line in iter(p.stdout.readline, b''):
        #     outputs += line.decode('GB2312')
        # p.stdout.close()
        # p.wait()
        # # logger.debug(cmd)
        # # logger.debug(outputs)
        # if 'Everything is Ok' in outputs:
        #     suc = True
    except Exception as e:
        logger.error("无法压缩zip文件")
        logger.debug(traceback.print_exc())
        logger.error(e)
    return suc


def _rar(srcPath, dstPath, overwrite=False, passwd=None):
    """
    压缩rar文件
    :param srcPath: 支持传入文件列表
    :param dstPath:
    :param overwrite: 是否覆盖已有rar文件
    :param passwd: 密码
    :return: 压缩rar文件是否成功
    """
    suc = False
    logger.debug("正在压缩rar文件...")
    winRarPath = r'..\Python\python3_lib\Scripts\WinRAR\Rar.exe'
    # 转为列表方便后续判断
    target_path = srcPath
    if isinstance(srcPath, str):
        target_path = [srcPath]

    if dstPath in target_path:
        logger.error("无法压缩rar文件，源文件路径与目标文件路径不能相同！")
        return suc
    if not all(os.path.exists(t_path) for t_path in target_path):
        logger.error("无法压缩rar文件，源文件不存在！")
        return suc
    if not dstPath.lower().endswith('.rar'):
        logger.error("无法压缩rar文件，目标文件不是rar文件！")
        return suc
    if overwrite is False and os.path.exists(dstPath):
        logger.error("无法压缩rar文件，目标文件已存在，且不覆盖！")
        return suc

    target_path = " ".join(target_path)
    try:
        outputs = ''
        if platform.system() == "Windows":
            # 必须先移除同名文件，否则会直接在原有压缩文件内添加新文件
            if overwrite and os.path.exists(dstPath):
                os.remove(dstPath)

            if passwd:
                cmd = winRarPath + f' a -ep1 -p{passwd} {dstPath} {srcPath}'
            else:
                cmd = winRarPath + f' a -ep1 "{dstPath}" "{srcPath}"'
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1)
            for line in iter(p.stdout.readline, b''):
                outputs += line.decode('GB2312')
            p.stdout.close()
            p.wait()
            if '已完成' in outputs:
                suc = True
        else:
            logger.error('无法压缩rar文件，暂不支持非Windows平台！')
            return suc
    except Exception as e:
        logger.error("无法压缩rar文件")
        logger.debug(traceback.print_exc())
        logger.error(e)
    return suc


def _uncompress(srcPath, dstPath, overwrite=False, passwd=None):
    """
    解压缩rar文件
    :param srcPath: 源rar文件
    :param dstPath: 目标目录
    :param overwrite: 是否覆盖
    :param passwd: 密码
    :return: 解压缩rar文件是否成功
    """
    suc = False
    logger.debug(f"正在解压缩{srcPath[-3:]}文件...")
    zip_exe_path = r'..\Python\python3_lib\Scripts\7z1900-extra\7z.exe'
    try:
        outputs = ''
        if platform.system() == "Windows":
            if not overwrite:
                ## 获取下压缩包的所有文件名
                outputs = list()
                cmd = '{zip_exe_path}  l "{srcPath}"   {passwd}'.format(zip_exe_path=zip_exe_path,srcPath=srcPath,passwd=passwd)
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1)
                for line in iter(p.stdout.readline, b''):
                    outputs.append(line.decode('GB2312').strip())
                p.stdout.close()
                tag = False
                for output in outputs:
                    if "------------------" in output:
                        tag = not tag
                        continue
                    if tag:
                        # file_name = output.split()[-1] # 考虑到文件名带空格的情况，不能直接以空格切割
                        file_name=output[53:]
                        if os.path.exists(os.path.join(dstPath,file_name)) and not os.path.isdir(os.path.join(dstPath,file_name)):
                            logger.error(f"无法解压缩文件，存在同名文件：{os.path.join(dstPath,file_name)} ")
                            return suc
            outputs = ''
            overwrite_cmd = '-aoa' if overwrite else '-aos'
            passwd_cmd = '-p' + str(passwd) if passwd else '-p'
            # .\7z.exe -aoa x D:\演示\演示.rar -oD:\演示-目标\ -p
            cmd = zip_exe_path + ' {overwrite_cmd} x "{srcPath}" -o"{dstPath}" {passwd_cmd}'
            # logger.debug(cmd)
            cmd = cmd.format(overwrite_cmd=overwrite_cmd, srcPath=srcPath, dstPath=dstPath, passwd_cmd=passwd_cmd)
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE, bufsize=1)

            outputs,error = p.communicate()
            if error.decode('GB2312')!="":
                logger.error(error.decode('GB2312').strip())
                return suc
            if 'ERROR: Wrong password' in outputs.decode('GB2312'):
                logger.error('无法解压缩文件，密码错误！')
                return suc
            if 'Everything is Ok' in outputs.decode('GB2312'):
                suc = True
        else:
            logger.error('无法解压缩文件，暂不支持非Windows平台！')
            return suc
    except RuntimeError as e:
        error_log = str(e.args)
        if 'Bad password' in error_log:
            logger.error('无法解压缩文件，密码错误！')
        logger.error("无法解压缩文件")
        logger.debug(traceback.print_exc())
        logger.error(e)
    return suc


def archive(srcPath, dstPath, archive_type='zip', overwrite=False, passwd=None):
    """
    压缩文件，目前只支持zip格式压缩
    :param srcPath: 被压缩文件，支持传入文件列表
    :param dstPath: 压缩文件路径
    :param archive_type: 压缩格式
    :param overwrite: 是否覆盖已有压缩文件
    :param passwd: 密码
    :return: 是否压缩成功
    """
    if archive_type == 'zip':
        return _zip(srcPath, dstPath, overwrite=overwrite, passwd=passwd)
    if archive_type == 'rar':
        return _rar(srcPath, dstPath, overwrite=overwrite, passwd=passwd)
    else:
        logger.error("无法压缩文件，暂不支持此类型格式压缩！")
        return False


def extract(srcPath, dstPath, overwrite=False, passwd=None):
    """
    解压缩文件
    :param srcPath: 源压缩文件
    :param dstPath: 目标目录
    :param overwrite: 是否覆盖已有文件
    :param passwd: 密码
    :return: 是否解压缩成功
    """
    suc = False
    if srcPath == dstPath:
        logger.error("无法压解缩文件，源文件路径与目标文件路径不能相同！")
        return suc
    if not os.path.exists(srcPath):
        logger.error("无法解压缩文件，源文件不存在！")
        return suc

    if sys.platform.lower()=="linux" and srcPath.lower().endswith('.zip'):
        return _unzip(srcPath,dstPath=dstPath,overwrite=overwrite,passwd=passwd)

    if srcPath.lower().endswith('.zip') or srcPath.lower().endswith('.rar'):
        return _uncompress(srcPath, dstPath, overwrite=overwrite, passwd=passwd)
    else:
        logger.error("无法解压缩zip文件，暂不支持此类型格式文件解压缩！")
        return suc


def base64ToFile(base64Str='', filePath='', continueOnFailure=False, errMsg=''):
    """
    base64字符串保存成文件
    :param base64Str:
    :param filePath:
    :param continueOnFailure:
    :param errMsg:
    :return:
    """
    logger.info(f'base64保存成图片至--{filePath}')
    try:
        if base64Str.startswith('data:image/png;base64,'):
            base64Str = base64Str[22:]
        dirname = os.path.dirname(filePath)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filePath, 'wb') as f:
            f.write(base64.b64decode(base64Str))
        return True
    except Exception as e:
        logger.error('保存base64为图片失败！')
        errMsg = errMsg if errMsg else e
        if continueOnFailure:
            return False
        else:
            raise Exception(errMsg)


def picTobase64(filePath='', continueOnFailure=False, errMsg=''):
    """
    图片转为base64
    :param filePath:
    :param continueOnFailure:
    :param errMsg:
    :return:
    """
    logger.info(f'{filePath}--图片转换成base64')
    try:
        if not os.path.exists(filePath):
            logger.error('图片文件不存在！')
        with open(filePath, 'rb') as f:
            picBase64 = base64.b64encode(f.read())
        return picBase64.decode()
    except Exception as e:
        logger.error('图片转base64失败！')
        errMsg = errMsg if errMsg else e
        if continueOnFailure:
            return ''
        else:
            raise Exception(errMsg)


if __name__=="__main__":
    # with open(r"D:\新建文件夹 (3)\新建文件夹\新建文本文档.txt","rb") as f:
    #     print(f.read())
    archive(srcPath=[r'D:\新建文件夹 (3)\新建文件夹\新建文本文档2.txt',r"D:\新建文件夹 (3)\新建文件夹\des"], dstPath=r'D:\新建文件夹 (3)\新建文件夹\test.zip', archive_type='zip',
                 overwrite=True, passwd='123')

    _unzip(srcPath=r"D:\新建文件夹 (3)\新建文件夹\test.zip",dstPath=r"D:\新建文件夹 (3)\新建文件夹\unzip",overwrite=True)