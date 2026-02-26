# src/sentiment/predictor.py
"""
统一情感分析预测器 - 吸收自 BettaFish SentimentAnalysisModel

设计模式吸收:
- BaseModel 抽象基类 → 统一 train/predict/evaluate/save/load 接口
- SentimentPredictor → 多模型管理 + predict_single/predict_batch/ensemble_predict
- 集成投票 → 加权投票融合多个模型的预测结果

当前实现使用 DeepSeek LLM 作为主力模型，保留多模型扩展架构
"""
import json
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════
# 抽象基类 - 吸收自 BettaFish base_model.py
# ═══════════════════════════════════════════

class BaseModel(ABC):
    """情感分析模型抽象基类"""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.is_loaded = False

    @abstractmethod
    def predict_single(self, text: str) -> Tuple[int, float]:
        """预测单条文本 → (label, confidence)  label: 1=正面, 0=负面"""
        pass

    @abstractmethod
    def predict_batch(self, texts: List[str]) -> List[Dict]:
        """批量预测 → [{text, label, sentiment, confidence}, ...]"""
        pass

    def get_info(self) -> Dict:
        """模型信息"""
        return {
            "name": self.model_name,
            "is_loaded": self.is_loaded,
        }


# ═══════════════════════════════════════════
# DeepSeek LLM 模型 - 本项目的主力模型
# ═══════════════════════════════════════════

class DeepSeekModel(BaseModel):
    """基于 DeepSeek LLM 的情感分析模型"""

    def __init__(self):
        super().__init__("deepseek-llm")
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            from src.config import get_deepseek_llm
            self._llm = get_deepseek_llm()
            self.is_loaded = True
        return self._llm

    def predict_single(self, text: str) -> Tuple[int, float]:
        llm = self._get_llm()
        prompt = f"""分析以下文本的情感倾向，返回JSON格式：
{{"sentiment": "positive/negative/neutral", "confidence": 0.0-1.0, "emotions": ["情绪词1"]}}

文本: {text[:500]}

只返回JSON，不要其他内容。"""
        try:
            response = llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                data = json.loads(match.group())
                sentiment = data.get("sentiment", "neutral")
                confidence = float(data.get("confidence", 0.5))
                label = 1 if sentiment == "positive" else (0 if sentiment == "negative" else -1)
                return label, confidence
            return -1, 0.5
        except Exception as e:
            logger.error(f"[DeepSeekModel] 预测失败: {e}")
            return -1, 0.0

    def predict_batch(self, texts: List[str]) -> List[Dict]:
        results = []
        for text in texts:
            label, conf = self.predict_single(text)
            sentiment = "positive" if label == 1 else ("negative" if label == 0 else "neutral")
            results.append({
                "text": text[:100],
                "label": label,
                "sentiment": sentiment,
                "confidence": conf,
                "model": self.model_name,
            })
        return results


# ═══════════════════════════════════════════
# LangChain Tool 模型 - 使用已有的 sentiment_tool
# ═══════════════════════════════════════════

class LangChainToolModel(BaseModel):
    """封装已有的 LangChain sentiment_tool"""

    def __init__(self):
        super().__init__("langchain-tool")
        self._tool = None

    def _get_tool(self):
        if self._tool is None:
            from src.tools.sentiment_tool import sentiment_analyzer
            self._tool = sentiment_analyzer
            self.is_loaded = True
        return self._tool

    def predict_single(self, text: str) -> Tuple[int, float]:
        tool = self._get_tool()
        try:
            result = json.loads(tool.invoke(text))
            sentiment = result.get("sentiment", "neutral")
            confidence = float(result.get("confidence", 0.5))
            label = 1 if sentiment == "positive" else (0 if sentiment == "negative" else -1)
            return label, confidence
        except Exception as e:
            logger.error(f"[LangChainToolModel] 预测失败: {e}")
            return -1, 0.0

    def predict_batch(self, texts: List[str]) -> List[Dict]:
        tool = self._get_tool()
        results = []
        for text in texts:
            try:
                raw = json.loads(tool.invoke(text))
                results.append({
                    "text": text[:100],
                    "label": 1 if raw.get("sentiment") == "positive" else (0 if raw.get("sentiment") == "negative" else -1),
                    "sentiment": raw.get("sentiment", "neutral"),
                    "confidence": float(raw.get("confidence", 0.5)),
                    "emotions": raw.get("emotions", []),
                    "model": self.model_name,
                })
            except Exception as e:
                results.append({"text": text[:100], "label": -1, "sentiment": "neutral", "confidence": 0, "model": self.model_name, "error": str(e)})
        return results


# ═══════════════════════════════════════════
# 统一预测器 - 核心吸收自 BettaFish SentimentPredictor
# ═══════════════════════════════════════════

class SentimentPredictor:
    """
    统一情感分析预测器

    核心设计吸收自 BettaFish SentimentAnalysisModel/predict.py：
    - 多模型注册与管理
    - predict_single / predict_batch 统一接口
    - ensemble_predict 集成投票（加权多数投票）
    - 可扩展：只需继承 BaseModel 并注册即可添加新模型
    """

    def __init__(self):
        self.models: Dict[str, BaseModel] = {}
        # 默认注册两个内置模型
        self.register_model(LangChainToolModel())
        self.register_model(DeepSeekModel())

    def register_model(self, model: BaseModel) -> None:
        """注册模型"""
        self.models[model.model_name] = model

    def get_available_models(self) -> List[Dict]:
        """获取可用模型列表"""
        return [
            {**m.get_info(), "type": "llm" if "llm" in m.model_name or "deepseek" in m.model_name else "tool"}
            for m in self.models.values()
        ]

    def predict_single(self, text: str, model_name: Optional[str] = None) -> Dict:
        """
        预测单条文本情感

        Args:
            text: 待分析文本
            model_name: 指定模型名，None 使用默认模型(langchain-tool)

        Returns:
            {text, sentiment, confidence, label, model, emotions?}
        """
        if model_name:
            if model_name not in self.models:
                raise ValueError(f"模型 {model_name} 未注册，可用: {list(self.models.keys())}")
            model = self.models[model_name]
        else:
            model = self.models.get("langchain-tool") or list(self.models.values())[0]

        label, conf = model.predict_single(text)
        sentiment = "positive" if label == 1 else ("negative" if label == 0 else "neutral")
        return {
            "text": text[:100],
            "sentiment": sentiment,
            "label": label,
            "confidence": conf,
            "model": model.model_name,
        }

    def predict_batch(self, texts: List[str], model_name: Optional[str] = None) -> List[Dict]:
        """批量预测"""
        if model_name:
            if model_name not in self.models:
                raise ValueError(f"模型 {model_name} 未注册")
            return self.models[model_name].predict_batch(texts)
        model = self.models.get("langchain-tool") or list(self.models.values())[0]
        return model.predict_batch(texts)

    def ensemble_predict(self, text: str, weights: Optional[Dict[str, float]] = None) -> Dict:
        """
        集成预测 - 多模型加权投票

        吸收自 BettaFish SentimentPredictor.ensemble_predict()
        """
        if len(self.models) == 0:
            raise ValueError("没有注册任何模型")

        if weights is None:
            weights = {name: 1.0 for name in self.models}

        total_weight = 0
        weighted_positive = 0

        individual_results = {}
        for name, model in self.models.items():
            if name not in weights:
                continue
            try:
                label, conf = model.predict_single(text)
                individual_results[name] = {"label": label, "confidence": conf}
                w = weights[name]
                # 转换为正面概率
                if label == 1:
                    prob = conf
                elif label == 0:
                    prob = 1.0 - conf
                else:
                    prob = 0.5
                weighted_positive += prob * w
                total_weight += w
            except Exception as e:
                logger.warning(f"[Ensemble] 模型 {name} 失败: {e}")

        if total_weight == 0:
            return {"sentiment": "neutral", "label": -1, "confidence": 0, "model": "ensemble"}

        final_prob = weighted_positive / total_weight
        final_label = 1 if final_prob > 0.55 else (0 if final_prob < 0.45 else -1)
        final_sentiment = "positive" if final_label == 1 else ("negative" if final_label == 0 else "neutral")
        final_conf = final_prob if final_label == 1 else (1 - final_prob if final_label == 0 else abs(final_prob - 0.5) * 2)

        return {
            "text": text[:100],
            "sentiment": final_sentiment,
            "label": final_label,
            "confidence": round(final_conf, 4),
            "model": "ensemble",
            "individual_results": individual_results,
        }
