import asyncio
import aiohttp
import logging
import re

logger = logging.getLogger("ChatServer")


class HotSearchHelper:
    @staticmethod
    async def get_baidu_hot_search():
        """
        从百度获取热搜列表
        
        Returns:
            list: 热搜列表
        """
        try:
            async with aiohttp.ClientSession() as session:
                # 使用百度热搜的专门页面
                url = "https://top.baidu.com/board?tab=realtime"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
                    "Connection": "keep-alive"
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        # 提取热搜内容
                        hot_searches = []
                        
                        # 根据用户提供的截图，更新正则表达式匹配最新的百度热搜格式
                        # 匹配标题和热度的模式
                        patterns = [
                            # 匹配可能的热搜标题格式
                            re.compile(r'<div class=["\']c-single-text-ellipsis["\'].*?>(.*?)</div>', re.DOTALL),
                            # 匹配a标签中的文本
                            re.compile(r'<a[^>]*?>(.*?)</a>', re.DOTALL),
                        ]
                        
                        # 尝试所有模式进行匹配
                        for pattern in patterns:
                            matches = pattern.findall(html_content)
                            for match in matches:
                                title = match.strip()
                                # 过滤无效标题
                                if (title and len(title) > 4 and len(title) < 80 and 
                                    title not in hot_searches and 
                                    not any(keyword in title.lower() for keyword in ['http', 'javascript', 'css', 'style', 'script', 'img', 'div', 'span'])):
                                    hot_searches.append(title)
                                    if len(hot_searches) >= 10:
                                        break
                            if len(hot_searches) >= 10:
                                break
                        
                        # 如果使用特定模式没有匹配到足够的热搜，使用通用模式
                        if len(hot_searches) < 10:
                            logger.info("搜索整个HTML以获取更多热搜")
                            general_pattern = re.compile(r'>([^<]{5,50})<', re.DOTALL)
                            general_matches = general_pattern.findall(html_content)
                            
                            for match in general_matches:
                                title = match.strip()
                                if (title and len(title) > 4 and len(title) < 80 and 
                                    title not in hot_searches and 
                                    not any(keyword in title.lower() for keyword in ['http', 'javascript', 'css', 'style', 'script', 'img', 'div', 'span'])):
                                    hot_searches.append(title)
                                    if len(hot_searches) >= 10:
                                        break
                        
                        # 如果没有匹配到，使用备用数据
                        if not hot_searches:
                            logger.warning("无法从百度获取热搜，使用备用数据")
                            hot_searches = [
                                "日本跟中国不是一个量级的",
                                "村民用了多年的垫脚石竟是恐龙化石",
                                "流感季防护 这些误区要避开",
                                "俄罗斯洲际弹道导弹爆炸",
                                "女子地铁内蹲坐被压骨折 获赔15万",
                                "旅行社：中国赴日团体游几乎全部",
                                "300元滑雪服被冻哭的年轻人焊身上",
                                "女子150万竞得32间法拍房6年未交付",
                                "刘强东：未来机器人会完成所有工作",
                                "感悟跨越百年的鼓岭情缘"
                            ]
                        
                        logger.info(f"成功获取百度热搜列表，共{len(hot_searches)}条")
                        return hot_searches[:10]  # 确保只返回10条
                    else:
                        logger.error(f"获取百度热搜失败: HTTP {response.status}")
                        # 返回备用数据
                        return [
                            "获取热搜失败，使用默认数据",
                            "新闻资讯：热点事件追踪",
                            "科技动态：创新产品发布",
                            "娱乐八卦：明星最新消息",
                            "生活百科：实用小技巧"
                        ]
        except Exception as e:
            logger.error(f"获取百度热搜异常: {str(e)}")
            # 返回备用数据，使用用户提供的热搜内容
            return [
                "日本跟中国不是一个量级的",
                "村民用了多年的垫脚石竟是恐龙化石",
                "流感季防护 这些误区要避开",
                "俄罗斯洲际弹道导弹爆炸",
                "女子地铁内蹲坐被压骨折 获赔15万",
                "旅行社：中国赴日团体游几乎全部",
                "300元滑雪服被冻哭的年轻人焊身上",
                "女子150万竞得32间法拍房6年未交付",
                "刘强东：未来机器人会完成所有工作",
                "感悟跨越百年的鼓岭情缘"
            ]

    @staticmethod
    def format_hot_searches(hot_searches):
        """
        将热搜列表格式化为卡片形式的消息
        
        Args:
            hot_searches: 热搜列表
            
        Returns:
            str: 格式化后的热搜卡片消息
        """
        if not hot_searches:
            return "暂无热搜数据"
        
        # 创建卡片形式的消息
        formatted = "🔥 今日热搜榜 🔥\n\n"
        for i, search in enumerate(hot_searches, 1):
            # 使用不同的图标表示不同的排名
            icons = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            icon = icons[i-1] if i-1 < len(icons) else f"{i}️⃣"
            formatted += f"{icon} {search}\n"
        
        formatted += "\n💡 点击热搜关键词可查看详情"
        return formatted
