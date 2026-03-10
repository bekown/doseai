# app/utils/ai_service.py

import os
import json
from datetime import datetime
from flask import current_app
from .cache_service import cache

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class AIService:
    """Service for AI-powered features"""
    
    def __init__(self):
        self.api_key = current_app.config.get('GEMINI_API_KEY')
        self.model_name = current_app.config.get('AI_MODEL_NAME', 'gemini-2.0-flash-exp')
        self.temperature = current_app.config.get('AI_TEMPERATURE', 0.1)
        
        if GEMINI_AVAILABLE and self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None
    
    def generate_medication_summary(self, medication_data):
        """Generate AI summary for a medication"""
        cache_key = f"med_summary_{medication_data.get('name', '')}"
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        if not self.model:
            return self._get_fallback_summary(medication_data)
        
        prompt = f"""
        Generate a patient-friendly summary for the medication: {medication_data.get('name', 'Unknown')}
        Strength: {medication_data.get('strength', 'Unknown')}
        Form: {medication_data.get('form', 'Unknown')}
        
        Include:
        1. Common uses
        2. How to take it
        3. Common side effects
        4. Important warnings
        5. What to do if you miss a dose
        
        Keep it concise and easy to understand.
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': self.temperature,
                    'max_output_tokens': 500,
                }
            )
            summary = response.text
            cache.set(cache_key, summary, timeout=86400)  # Cache for 24 hours
            return summary
        except Exception as e:
            current_app.logger.error(f"AI summary generation failed: {e}")
            return self._get_fallback_summary(medication_data)
    
    def check_drug_interactions(self, medications_list):
        """Check for potential drug interactions"""
        cache_key = f"interactions_{hash(str(medications_list))}"
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        if not self.model:
            return []
        
        medications_text = "\n".join([f"- {med}" for med in medications_list])
        
        prompt = f"""
        Analyze these medications for potential interactions:
        {medications_text}
        
        Return JSON format:
        {{
            "interactions": [
                {{
                    "medication1": "name",
                    "medication2": "name",
                    "severity": "major|moderate|minor",
                    "description": "brief description",
                    "recommendation": "what to do"
                }}
            ]
        }}
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,
                    'max_output_tokens': 1000,
                }
            )
            
            # Parse JSON response
            content = response.text.strip()
            if content.startswith('```json'):
                content = content[7:-3]  # Remove markdown code blocks
            
            result = json.loads(content)
            cache.set(cache_key, result, timeout=3600)  # Cache for 1 hour
            return result.get('interactions', [])
        except Exception as e:
            current_app.logger.error(f"AI interaction check failed: {e}")
            return []
    
    def generate_health_insights(self, user_data):
        """Generate personalized health insights"""
        if not self.model:
            return self._get_fallback_insights()
        
        prompt = f"""
        Based on this health data, provide 3 actionable insights:
        
        Medication Adherence: {user_data.get('adherence_rate', 0)}%
        Active Symptoms: {user_data.get('symptoms_count', 0)}
        Latest Vitals: {user_data.get('vitals_summary', 'Not available')}
        Medication Count: {user_data.get('medication_count', 0)}
        
        Format as JSON:
        {{
            "insights": [
                {{
                    "title": "Insight title",
                    "description": "Detailed description",
                    "priority": "high|medium|low",
                    "action": "suggested action",
                    "category": "adherence|symptoms|medication|general"
                }}
            ]
        }}
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.2,
                    'max_output_tokens': 800,
                }
            )
            
            content = response.text.strip()
            if content.startswith('```json'):
                content = content[7:-3]
            
            return json.loads(content).get('insights', [])
        except Exception as e:
            current_app.logger.error(f"AI insights generation failed: {e}")
            return self._get_fallback_insights()
    
    def _get_fallback_summary(self, medication_data):
        """Fallback summary when AI is unavailable"""
        return f"""
        <strong>{medication_data.get('name', 'Medication')}</strong>
        <p>Strength: {medication_data.get('strength', 'Not specified')}</p>
        <p>Form: {medication_data.get('form', 'Not specified')}</p>
        <p>Take as prescribed by your healthcare provider. Contact your doctor if you experience unusual side effects.</p>
        """
    
    def _get_fallback_insights(self):
        """Fallback insights when AI is unavailable"""
        return [
            {
                'title': 'Continue Medication Adherence',
                'description': 'Keep taking your medications as prescribed for best results.',
                'priority': 'medium',
                'action': 'Set reminders for your medications',
                'category': 'adherence'
            }
        ]