import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建SixtySecondHelper类用于导出
class SixtySecondHelper:
    # 类级别的常量和方法

    # 类级别的常量和方法
    # 常量定义
    URL = "https://blog.intelexe.cn/display_images.php"
    # 修正为相对于服务器的路径
    STATUS_FILE = os.path.join(os.path.dirname(__file__), "status.json")
    # 图片保存到client/images目录下
    IMAGE_OUTPUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "client", "images", "news.png")
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0"

    # 请求头
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,en-GB;q=0.6",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    @staticmethod
    def get_page_content():
        """
        获取页面内容
        :return: 页面HTML内容，如果获取失败返回None
        """
        try:
            logger.info(f"正在获取页面内容: {SixtySecondHelper.URL}")
            # 添加重试机制
            max_retries = 3
            for retry in range(max_retries):
                try:
                    response = requests.get(SixtySecondHelper.URL, headers=SixtySecondHelper.headers, timeout=30)
                    response.raise_for_status()  # 检查HTTP状态码
                    logger.info(f"成功获取页面内容，状态码: {response.status_code}")
                    # 记录响应头信息，有助于调试
                    logger.debug(f"响应头: {dict(response.headers)}")
                    return response.text
                except requests.exceptions.RequestException as e:
                    if retry < max_retries - 1:
                        logger.warning(f"获取页面失败，正在重试 ({retry + 1}/{max_retries}): {e}")
                        time.sleep(2)  # 等待2秒后重试
                    else:
                        logger.error(f"获取页面内容失败（已尝试{max_retries}次）: {e}")
                        return None
        except Exception as e:
            logger.error(f"获取页面内容时发生未知错误: {e}")
            return None

    @staticmethod
    def check_update_status(html_content):
        """
        检查更新状态
        :param html_content: 页面HTML内容
        :return: 如果更新状态为"今日已更新"返回True，否则返回False
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 方法1：直接查找id为update_hint的元素
            update_hint = soup.find(id="update_hint")
            if update_hint:
                status_text = update_hint.get_text().strip()
                logger.info(f"通过ID找到更新状态: {status_text}")
                return "今日已更新" in status_text
            
            # 方法2：查找包含"今日已更新"文本的任何元素
            elements_with_text = soup.find_all(string=lambda text: text and "今日已更新" in text)
            if elements_with_text:
                for element in elements_with_text:
                    parent = element.find_parent()
                    if parent:
                        logger.info(f"通过文本找到更新状态元素: {parent.get_text().strip()}")
                        return True
            
            # 方法3：查找可能包含更新状态的常见标签
            common_tags = soup.find_all(['div', 'span', 'p', 'h1', 'h2', 'h3'])
            for tag in common_tags:
                text = tag.get_text().strip()
                if "今日已更新" in text:
                    logger.info(f"通过常见标签找到更新状态: {text}")
                    return True
            
            # 方法4：直接在HTML字符串中搜索
            if "今日已更新" in html_content:
                logger.info("在HTML内容中找到'今日已更新'文本")
                return True
            
            logger.warning("未找到更新状态元素或文本")
            return False
        except Exception as e:
            logger.error(f"检查更新状态时出错: {e}")
            return False

    @staticmethod
    def get_today_date_str():
        """
        获取今天的日期字符串，格式为YYYY-MM-DD
        :return: 日期字符串
        """
        return datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def get_today_date_code():
        """
        获取今天的日期编号，格式为YYYYMMDD
        :return: 日期编号字符串
        """
        return datetime.now().strftime("%Y%m%d")

    @staticmethod
    def extract_image_url(html_content):
        """
        提取图片URL（使用备用方案）
        :param html_content: 页面HTML内容
        :return: 图片的绝对URL
        """
        try:
            # 使用备用方案：直接构造图片URL
            today_code = SixtySecondHelper.get_today_date_code()
            img_url = f"https://blog.intelexe.cn/images/60秒_{today_code}_帆船网络.png"
            logger.info(f"使用备用方案构造图片URL: {img_url}")
            return img_url
        except Exception as e:
            logger.error(f"构造图片URL时出错: {e}")
            return None

    @staticmethod
    def download_image(image_url, output_path):
        """
        下载图片
        :param image_url: 图片URL
        :param output_path: 输出路径
        :return: 下载成功返回True，否则返回False
        """
        try:
            logger.info(f"正在下载图片: {image_url}")
            
            # 添加重试机制
            max_retries = 3
            for retry in range(max_retries):
                try:
                    response = requests.get(image_url, headers=SixtySecondHelper.headers, timeout=60, stream=True)
                    
                    # 检查是否为404错误
                    if response.status_code == 404:
                        logger.error(f"图片不存在（404错误）: {image_url}")
                        return False
                    
                    response.raise_for_status()
                    
                    # 检查响应内容类型是否为图片
                    content_type = response.headers.get('Content-Type', '')
                    if not content_type.startswith('image/'):
                        logger.warning(f"下载的内容不是图片，Content-Type: {content_type}")
                        # 仍然尝试保存，因为有时候服务器可能不会正确设置Content-Type
                    
                    # 确保文件目录存在
                    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                    
                    # 写入文件
                    with open(output_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    # 验证文件大小
                    file_size = os.path.getsize(output_path)
                    logger.info(f"图片下载成功: {output_path}, 文件大小: {file_size} 字节")
                    
                    # 检查文件是否为空
                    if file_size == 0:
                        logger.error("下载的图片文件为空")
                        os.remove(output_path)  # 删除空文件
                        return False
                    
                    return True
                except requests.exceptions.RequestException as e:
                    if retry < max_retries - 1:
                        logger.warning(f"下载图片失败，正在重试 ({retry + 1}/{max_retries}): {e}")
                        time.sleep(3)  # 等待3秒后重试
                    else:
                        logger.error(f"下载图片失败（已尝试{max_retries}次）: {e}")
                        return False
        except IOError as e:
            logger.error(f"保存图片失败: {e}")
            # 清理可能的不完整文件
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                    logger.info(f"已删除不完整的图片文件: {output_path}")
                except:
                    pass
            return False
        except Exception as e:
            logger.error(f"下载图片时发生未知错误: {e}")
            # 清理可能的不完整文件
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                    logger.info(f"已删除不完整的图片文件: {output_path}")
                except:
                    pass
            return False

    @staticmethod
    def get_current_timestamp():
        """
        获取当前时间戳
        :return: 时间戳
        """
        return datetime.now().isoformat()

    @staticmethod
    def load_status():
        """
        加载状态文件
        :return: 状态字典，如果文件不存在返回空字典
        """
        try:
            if os.path.exists(SixtySecondHelper.STATUS_FILE):
                with open(SixtySecondHelper.STATUS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"加载状态文件失败: {e}")
            return {}

    @staticmethod
    def save_status(status_data):
        """
        保存状态文件
        :param status_data: 要保存的状态数据
        :return: 保存成功返回True，否则返回False
        """
        try:
            with open(SixtySecondHelper.STATUS_FILE, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, ensure_ascii=False, indent=2)
            logger.info("状态文件保存成功")
            return True
        except IOError as e:
            logger.error(f"保存状态文件失败: {e}")
            return False

    @staticmethod
    def check_today_status():
        """
        检查今天是否已经正常爬取
        :return: 如果今天已经正常爬取返回True，否则返回False
        """
        today = SixtySecondHelper.get_today_date_str()
        status = SixtySecondHelper.load_status()
        
        # 检查是否有今天的记录，并且状态是正常爬取
        if today in status and status[today].get("success", False):
            logger.info(f"今天({today})已经正常爬取过")
            return True
        return False

    @staticmethod
    def update_today_status(success):
        """
        更新今天的爬取状态
        :param success: 是否正常爬取
        :return: 更新成功返回True，否则返回False
        """
        today = SixtySecondHelper.get_today_date_str()
        timestamp = SixtySecondHelper.get_current_timestamp()
        
        # 加载现有状态
        status = SixtySecondHelper.load_status()
        
        # 更新今天的状态
        status[today] = {
            "timestamp": timestamp,
            "success": success
        }
        
        return SixtySecondHelper.save_status(status)

    @staticmethod
    def main():
        """
        主函数
        :return: True代表正常爬取，False代表爬取失败，如果当天已经正常爬取过也返回True
        """
        start_time = time.time()
        logger.info("=" * 50)
        logger.info(f"开始执行爬虫任务: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 检查环境
            logger.info(f"程序运行目录: {os.getcwd()}")
            
            # 检查今天是否已经正常爬取过
            if SixtySecondHelper.check_today_status():
                logger.info("任务提前结束：今天已经正常爬取过")
                return True
            
            # 获取页面内容
            logger.info("步骤1: 获取页面内容")
            html_content = SixtySecondHelper.get_page_content()
            if not html_content:
                # 获取页面失败，更新状态为失败
                logger.error("步骤1失败: 获取页面内容失败")
                SixtySecondHelper.update_today_status(False)
                return False
            
            # 检查页面内容是否合理
            if len(html_content) < 1000:
                logger.warning(f"页面内容异常简短，长度: {len(html_content)} 字符")
                # 仍然继续尝试处理，但标记为警告
            
            # 检查更新状态
            logger.info("步骤2: 检查更新状态")
            if not SixtySecondHelper.check_update_status(html_content):
                # 未更新，更新状态为失败
                logger.info("步骤2结果: 内容未更新，无需下载图片")
                SixtySecondHelper.update_today_status(False)
                return False
            
            # 提取图片URL
            logger.info("步骤3: 提取图片URL")
            image_url = SixtySecondHelper.extract_image_url(html_content)
            if not image_url:
                # 提取图片URL失败，更新状态为失败
                logger.error("步骤3失败: 提取图片URL失败")
                SixtySecondHelper.update_today_status(False)
                return False
            
            # 下载图片
            logger.info("步骤4: 下载图片")
            if SixtySecondHelper.download_image(image_url, SixtySecondHelper.IMAGE_OUTPUT):
                # 下载成功，更新状态为成功
                logger.info("步骤4成功: 图片下载完成")
                SixtySecondHelper.update_today_status(True)
                
                # 验证下载的图片文件
                if os.path.exists(SixtySecondHelper.IMAGE_OUTPUT):
                    file_size = os.path.getsize(SixtySecondHelper.IMAGE_OUTPUT)
                    logger.info(f"下载结果验证: 文件已存在，大小: {file_size} 字节")
                
                logger.info("爬虫任务执行成功")
                return True
            else:
                # 下载失败，更新状态为失败
                logger.error("步骤4失败: 下载图片失败")
                SixtySecondHelper.update_today_status(False)
                return False
        
        except Exception as e:
            # 捕获其他异常，更新状态为失败
            logger.error(f"爬虫执行过程中发生异常: {e}", exc_info=True)
            try:
                SixtySecondHelper.update_today_status(False)
            except:
                logger.error("更新状态文件失败")
            return False
        finally:
            # 记录任务执行时间
            end_time = time.time()
            logger.info(f"爬虫任务执行完成，耗时: {end_time - start_time:.2f} 秒")
            logger.info("=" * 50)

# 非类方法的调用支持（用于直接运行脚本）
if __name__ == "__main__":
    result = SixtySecondHelper.main()
    logger.info(f"爬虫任务执行结果: {'成功' if result else '失败'}")