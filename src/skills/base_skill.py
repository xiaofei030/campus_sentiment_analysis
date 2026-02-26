# src/skills/base_skill.py
"""
Skill 基础框架 - 可插拔技能模块系统
每个 Skill 是一个独立的能力单元，可以被 Agent 动态调用

设计理念：
- 每个 Skill 声明自己的 名称、描述、能力
- SkillRegistry 统一管理所有已注册的 Skill
- Agent 通过 SkillRegistry 发现和调用 Skill
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime


class BaseSkill(ABC):
    """技能基类 - 所有 Skill 必须继承此类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """技能名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """技能描述"""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """技能支持的能力列表"""
        pass
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @abstractmethod
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行技能动作
        
        Args:
            action: 要执行的动作名称（需在 capabilities 中声明）
            params: 动作参数
            
        Returns:
            执行结果字典
        """
        pass
    
    def validate_action(self, action: str) -> bool:
        """验证动作是否有效"""
        return action in self.capabilities
    
    def get_info(self) -> dict:
        """获取技能信息"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": self.capabilities,
        }


class SkillRegistry:
    """
    技能注册中心 - 管理所有可用 Skill
    
    用法：
        registry = SkillRegistry()
        registry.register(DataAnalysisSkill(db_session))
        result = registry.invoke("data_analysis", "sentiment_distribution", {...})
    """
    
    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}
    
    def register(self, skill: BaseSkill) -> None:
        """注册一个技能"""
        self._skills[skill.name] = skill
        print(f"[Skill] 已注册技能: {skill.name} (v{skill.version})")
    
    def unregister(self, skill_name: str) -> None:
        """注销一个技能"""
        if skill_name in self._skills:
            del self._skills[skill_name]
    
    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """获取指定技能"""
        return self._skills.get(skill_name)
    
    def list_skills(self) -> List[dict]:
        """列出所有已注册技能"""
        return [skill.get_info() for skill in self._skills.values()]
    
    def invoke(self, skill_name: str, action: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        调用技能
        
        Args:
            skill_name: 技能名称
            action: 动作名称
            params: 参数
            
        Returns:
            执行结果
        """
        skill = self._skills.get(skill_name)
        if not skill:
            return {"error": f"技能 '{skill_name}' 未注册", "available": list(self._skills.keys())}
        
        if not skill.validate_action(action):
            return {
                "error": f"技能 '{skill_name}' 不支持动作 '{action}'",
                "available_actions": skill.capabilities
            }
        
        try:
            result = skill.execute(action, params or {})
            result["_meta"] = {
                "skill": skill_name,
                "action": action,
                "timestamp": datetime.now().isoformat(),
            }
            return result
        except Exception as e:
            return {"error": str(e), "skill": skill_name, "action": action}
    
    def find_skill_for_action(self, action: str) -> Optional[str]:
        """根据动作名找到对应的技能"""
        for name, skill in self._skills.items():
            if action in skill.capabilities:
                return name
        return None
