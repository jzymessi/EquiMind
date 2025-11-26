"""
新闻获取工具 - 支持中文翻译
"""
from langchain.tools import BaseTool
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime, timedelta
from ..news_ingestor import ingest_once
from ..state_store import read_latest_news

class NewsTranslator:
    """新闻翻译器 - 简单的关键词翻译"""
    
    def __init__(self):
        self.finance_terms = {
            # 公司相关
            'earnings': '财报', 'revenue': '营收', 'profit': '利润', 'loss': '亏损',
            'quarterly': '季度', 'annual': '年度', 'guidance': '业绩指引',
            'dividend': '股息', 'buyback': '回购', 'merger': '并购', 'acquisition': '收购',
            
            # 市场相关
            'stock': '股票', 'shares': '股份', 'market': '市场', 'trading': '交易',
            'bull market': '牛市', 'bear market': '熊市', 'rally': '上涨', 'decline': '下跌',
            'volatility': '波动', 'volume': '成交量',
            
            # 财务指标
            'EPS': '每股收益', 'P/E': '市盈率', 'ROE': '净资产收益率',
            'cash flow': '现金流', 'debt': '债务', 'assets': '资产',
            
            # 行业相关
            'technology': '科技', 'semiconductor': '半导体', 'AI': '人工智能',
            'cloud': '云计算', 'software': '软件', 'hardware': '硬件',
            'automotive': '汽车', 'electric vehicle': '电动汽车', 'EV': '电动汽车',
            'healthcare': '医疗', 'pharmaceutical': '制药', 'biotech': '生物技术',
            
            # 动作词
            'announces': '宣布', 'reports': '发布', 'launches': '推出',
            'increases': '增加', 'decreases': '减少', 'beats': '超越',
            'misses': '未达', 'expects': '预期', 'forecasts': '预测'
        }
    
    def translate_title(self, title: str) -> str:
        """翻译标题中的关键财经术语"""
        translated = title
        for en_term, cn_term in self.finance_terms.items():
            # 简单替换，实际项目中可以使用更复杂的翻译API
            translated = translated.replace(en_term, f"{en_term}({cn_term})")
        return translated
    
    def translate_summary(self, summary: str) -> str:
        """翻译摘要"""
        if not summary or len(summary) < 10:
            return summary
            
        # 简单的关键词替换
        translated = summary
        for en_term, cn_term in self.finance_terms.items():
            translated = translated.replace(en_term, f"{en_term}({cn_term})")
        
        return translated[:300] + "..." if len(translated) > 300 else translated

class NewsRetrievalTool(BaseTool):
    name = "get_financial_news"
    description = "获取最新的财经新闻。输入：hours (获取最近N小时的新闻，默认24), limit (最大条数，默认10), keywords (可选的关键词过滤)。输出：中文翻译的新闻摘要。"

    def __init__(self):
        super().__init__()
        # 使用 object.__setattr__ 绕过 Pydantic 限制
        object.__setattr__(self, 'translator', NewsTranslator())

    def _run(self, hours: int = 24, limit: int = 10, keywords: str = None) -> str:
        try:
            # 1. 先尝试从本地获取新闻
            news_items = read_latest_news(limit=limit * 2)  # 多获取一些，便于过滤
            
            # 2. 如果本地新闻不够新，先抓取一次
            if not news_items or self._is_news_stale(news_items[0], hours):
                print("本地新闻过期，正在抓取最新新闻...")
                ingest_once()  # 抓取最新新闻
                news_items = read_latest_news(limit=limit * 2)
            
            if not news_items:
                return "暂时无法获取新闻，请稍后再试。"
            
            # 3. 过滤时间范围
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            recent_news = []
            
            for item in news_items:
                try:
                    pub_time = datetime.fromisoformat(item['published_at'].replace('Z', '+00:00'))
                    if pub_time.replace(tzinfo=None) > cutoff_time:
                        recent_news.append(item)
                except:
                    continue  # 跳过时间解析失败的新闻
            
            if not recent_news:
                return f"最近 {hours} 小时内暂无新闻更新。"
            
            # 4. 关键词过滤
            if keywords:
                filtered_news = self._filter_by_keywords(recent_news, keywords)
                if filtered_news:
                    recent_news = filtered_news
                else:
                    return f"最近 {hours} 小时内没有包含 '{keywords}' 的相关新闻。"
            
            # 5. 限制数量并翻译
            recent_news = recent_news[:limit]
            return self._format_news_response(recent_news, hours, keywords)
            
        except Exception as e:
            return f"获取新闻时出错：{str(e)}"

    def _is_news_stale(self, latest_news: Dict, max_hours: int) -> bool:
        """检查新闻是否过期"""
        try:
            pub_time = datetime.fromisoformat(latest_news['published_at'].replace('Z', '+00:00'))
            age_hours = (datetime.utcnow() - pub_time.replace(tzinfo=None)).total_seconds() / 3600
            return age_hours > max_hours
        except:
            return True

    def _filter_by_keywords(self, news_items: List[Dict], keywords: str) -> List[Dict]:
        """根据关键词过滤新闻"""
        keywords_list = [kw.strip().lower() for kw in keywords.split(',')]
        filtered = []
        
        for item in news_items:
            title_lower = item.get('title', '').lower()
            summary_lower = item.get('summary', '').lower()
            
            # 检查是否包含任一关键词
            if any(kw in title_lower or kw in summary_lower for kw in keywords_list):
                filtered.append(item)
        
        return filtered

    def _format_news_response(self, news_items: List[Dict], hours: int, keywords: Optional[str]) -> str:
        """格式化新闻响应"""
        header_parts = [f"📰 最近 {hours} 小时财经新闻"]
        if keywords:
            header_parts.append(f"(关键词: {keywords})")
        header_parts.append(f"(共 {len(news_items)} 条)\n")
        
        lines = ["".join(header_parts)]
        
        for i, item in enumerate(news_items, 1):
            # 翻译标题和摘要
            title = self.translator.translate_title(item.get('title', ''))
            summary = self.translator.translate_summary(item.get('summary', ''))
            source = item.get('source', 'unknown')
            
            # 格式化时间
            try:
                pub_time = datetime.fromisoformat(item['published_at'].replace('Z', '+00:00'))
                time_str = pub_time.strftime('%m-%d %H:%M')
            except:
                time_str = '时间未知'
            
            lines.append(f"{i}. 【{source.upper()}】{title}")
            if summary and len(summary.strip()) > 10:
                lines.append(f"   💡 {summary}")
            lines.append(f"   🕒 {time_str}")
            lines.append("")  # 空行分隔
        
        return "\n".join(lines)

    def _arun(self, **kwargs):
        raise NotImplementedError("异步暂不支持")


class MarketNewsAnalysisTool(BaseTool):
    name = "analyze_market_sentiment"
    description = "分析最近新闻的市场情绪。输入：hours (分析最近N小时，默认24), focus (关注领域，如'tech'、'ai'、'ev'等)。输出：市场情绪分析和投资建议。"

    def __init__(self):
        super().__init__()
        # 使用 object.__setattr__ 绕过 Pydantic 限制
        object.__setattr__(self, 'translator', NewsTranslator())

    def _run(self, hours: int = 24, focus: str = None) -> str:
        try:
            # 获取新闻
            news_tool = NewsRetrievalTool()
            keywords = self._get_focus_keywords(focus) if focus else None
            
            # 获取原始新闻数据
            news_items = read_latest_news(limit=50)
            if not news_items:
                return "无法获取新闻数据进行情绪分析。"
            
            # 简单的情绪分析
            sentiment_analysis = self._analyze_sentiment(news_items, hours, focus)
            return self._format_sentiment_response(sentiment_analysis, hours, focus)
            
        except Exception as e:
            return f"市场情绪分析出错：{str(e)}"

    def _get_focus_keywords(self, focus: str) -> str:
        """根据关注领域获取关键词"""
        focus_map = {
            'tech': 'technology,software,cloud,AI,semiconductor',
            'ai': 'AI,artificial intelligence,machine learning,ChatGPT,OpenAI',
            'ev': 'electric vehicle,EV,Tesla,battery,automotive',
            'crypto': 'bitcoin,cryptocurrency,blockchain,crypto',
            'healthcare': 'healthcare,pharmaceutical,biotech,drug,medical'
        }
        return focus_map.get(focus.lower(), focus)

    def _analyze_sentiment(self, news_items: List[Dict], hours: int, focus: Optional[str]) -> Dict:
        """简单的情绪分析"""
        positive_words = ['beats', 'exceeds', 'strong', 'growth', 'profit', 'gains', 'rises', 'up']
        negative_words = ['misses', 'falls', 'decline', 'loss', 'down', 'weak', 'concern', 'risk']
        
        sentiment_scores = []
        relevant_news = []
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        for item in news_items:
            try:
                pub_time = datetime.fromisoformat(item['published_at'].replace('Z', '+00:00'))
                if pub_time.replace(tzinfo=None) <= cutoff_time:
                    continue
                    
                title_lower = item.get('title', '').lower()
                summary_lower = item.get('summary', '').lower()
                text = f"{title_lower} {summary_lower}"
                
                # 计算情绪得分
                pos_count = sum(1 for word in positive_words if word in text)
                neg_count = sum(1 for word in negative_words if word in text)
                
                if pos_count > 0 or neg_count > 0:
                    score = (pos_count - neg_count) / (pos_count + neg_count + 1)
                    sentiment_scores.append(score)
                    relevant_news.append(item)
                    
            except:
                continue
        
        if not sentiment_scores:
            return {'sentiment': 'neutral', 'confidence': 0, 'news_count': 0}
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        
        if avg_sentiment > 0.2:
            sentiment = 'positive'
        elif avg_sentiment < -0.2:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'score': avg_sentiment,
            'confidence': min(len(sentiment_scores) / 10, 1.0),
            'news_count': len(relevant_news),
            'sample_news': relevant_news[:3]
        }

    def _format_sentiment_response(self, analysis: Dict, hours: int, focus: Optional[str]) -> str:
        """格式化情绪分析响应"""
        sentiment_emoji = {
            'positive': '📈 乐观',
            'negative': '📉 悲观', 
            'neutral': '📊 中性'
        }
        
        sentiment_text = sentiment_emoji.get(analysis['sentiment'], '❓ 未知')
        confidence = analysis['confidence'] * 100
        
        lines = [
            f"🎯 市场情绪分析报告",
            f"📅 时间范围: 最近 {hours} 小时"
        ]
        
        if focus:
            lines.append(f"🔍 关注领域: {focus}")
        
        lines.extend([
            f"📊 整体情绪: {sentiment_text}",
            f"🎚️  置信度: {confidence:.0f}%",
            f"📰 分析新闻: {analysis['news_count']} 条",
            ""
        ])
        
        if analysis.get('sample_news'):
            lines.append("📋 代表性新闻:")
            for i, news in enumerate(analysis['sample_news'], 1):
                title = self.translator.translate_title(news.get('title', ''))
                lines.append(f"{i}. {title}")
            lines.append("")
        
        # 投资建议
        if analysis['sentiment'] == 'positive' and confidence > 60:
            lines.append("💡 投资建议: 市场情绪偏乐观，可考虑适度增加仓位，但需注意风险控制。")
        elif analysis['sentiment'] == 'negative' and confidence > 60:
            lines.append("⚠️  投资建议: 市场情绪偏悲观，建议保持谨慎，可考虑减仓或观望。")
        else:
            lines.append("🤔 投资建议: 市场情绪中性，建议保持现有策略，关注具体个股机会。")
        
        return "\n".join(lines)

    def _arun(self, **kwargs):
        raise NotImplementedError("异步暂不支持")
