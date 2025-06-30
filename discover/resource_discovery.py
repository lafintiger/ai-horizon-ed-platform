"""
Resource Discovery Engine for AI-Horizon Ed

Uses Perplexity API to search for educational resources and AI to score content quality.
"""

import asyncio
import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import requests
from urllib.parse import urlparse

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import config

logger = logging.getLogger(__name__)

@dataclass
class DiscoveredResource:
    """Data class for a discovered educational resource"""
    title: str
    url: str
    description: str
    resource_type: str
    duration_estimate: Optional[int] = None  # minutes
    author: Optional[str] = None
    source_platform: Optional[str] = None
    keywords: List[str] = None
    raw_content: Optional[str] = None

class PerplexitySearcher:
    """Search for educational resources using Perplexity API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def search_educational_content(self, skill: str, resource_type: str = "all") -> List[DiscoveredResource]:
        """Search for educational content for a specific skill"""
        
        # Craft search prompts based on resource type
        search_prompts = self._generate_search_prompts(skill, resource_type)
        
        all_resources = []
        for prompt in search_prompts:
            try:
                resources = await self._execute_search(prompt, skill, resource_type)
                all_resources.extend(resources)
            except Exception as e:
                logger.error(f"Search failed for prompt '{prompt}': {e}")
        
        # Deduplicate based on URL
        seen_urls = set()
        unique_resources = []
        for resource in all_resources:
            if resource.url not in seen_urls:
                seen_urls.add(resource.url)
                unique_resources.append(resource)
        
        return unique_resources
    
    def _generate_search_prompts(self, skill: str, resource_type: str) -> List[str]:
        """Generate targeted search prompts based on AI workforce intelligence"""
        
        # Enhanced prompts based on real AI-cybersecurity workforce analysis
        ai_new_skills = [
            "prompt engineering", "ai security engineering", "mlsecops", 
            "ai governance", "ai security architecture"
        ]
        
        ai_augmented_skills = [
            "ai-enhanced", "ai-augmented", "threat intelligence", 
            "penetration testing", "threat hunting", "security research", "security analysis"
        ]
        
        skill_lower = skill.lower()
        is_ai_new = any(ai_skill in skill_lower for ai_skill in ai_new_skills)
        is_ai_augmented = any(aug_skill in skill_lower for aug_skill in ai_augmented_skills)
        
        if is_ai_new:
            # Prompts for entirely new AI-cybersecurity roles
            base_prompts = {
                "youtube_videos": [
                    f"Find cutting-edge YouTube content for '{skill}' - an emerging AI-cybersecurity role. Focus on: AI/ML security tutorials, practical frameworks, conference talks from DEF CON/Black Hat/BSides, hands-on labs, recent 2023-2024 content.",
                    f"Search for expert YouTube videos on {skill} including AI security implementation, real-world case studies, and practical demonstrations from cybersecurity conferences.",
                ],
                "online_courses": [
                    f"Find specialized online courses for '{skill}' covering AI security engineering, ML pipeline security, and AI governance. Include new certifications and emerging training programs.",
                    f"What are the latest {skill} courses focusing on AI/ML security implementation, practical labs, and industry-relevant training?",
                ],
                "documentation": [
                    f"Find technical documentation for '{skill}' including AI security frameworks, ML security guidelines, vendor documentation for AI security tools, and emerging industry standards.",
                    f"Search for official AI security documentation, whitepapers on {skill}, and technical guides for implementing AI-cybersecurity practices.",
                ],
                "tools": [
                    f"Find AI security tools, GitHub repositories, and platforms for practicing '{skill}'. Focus on ML security testing tools, AI governance platforms, and hands-on AI security labs.",
                    f"What are the best open-source tools and software for implementing {skill} in AI-cybersecurity environments?",
                ],
                "books": [
                    f"Find recent books on '{skill}' covering AI/ML security, emerging AI threats, and practical implementation guides for AI-cybersecurity professionals.",
                    f"Search for cutting-edge textbooks and references on {skill} with focus on practical AI security implementation.",
                ]
            }
        elif is_ai_augmented:
            # Prompts for AI-enhanced traditional cybersecurity roles
            base_prompts = {
                "youtube_videos": [
                    f"Find YouTube content showing how AI enhances '{skill}' work. Focus on: AI-powered security tools, automation workflows, before/after AI transformation, expert demonstrations, industry case studies.",
                    f"Search for videos demonstrating AI-augmented {skill} including practical tool implementations, workflow automation, and real-world AI integration examples.",
                ],
                "online_courses": [
                    f"Find courses on AI-enhanced {skill} covering AI-powered security platforms, automation integration, and transformation of traditional cybersecurity practices.",
                    f"What are the best courses showing how AI transforms {skill} work, including practical tool training and workflow automation?",
                ],
                "documentation": [
                    f"Find documentation on AI-powered {skill} tools, platforms that enhance traditional cybersecurity work, and guides for integrating AI into existing workflows.",
                    f"Search for technical guides on AI-augmented {skill} including tool documentation and integration best practices.",
                ],
                "tools": [
                    f"Find AI-powered tools that enhance {skill} work, including machine learning platforms, automation frameworks, and AI-integrated security tools.",
                    f"What are the best AI-enhanced tools for {skill} that augment human capabilities and automate routine tasks?",
                ],
                "books": [
                    f"Find books on AI transformation in {skill}, covering how AI enhances traditional cybersecurity work and practical implementation strategies.",
                    f"Search for literature on AI-augmented {skill} with focus on practical integration and workflow transformation.",
                ]
            }
        else:
            # Standard prompts for traditional cybersecurity skills
            base_prompts = {
                "youtube_videos": [
                    f"Find the best YouTube tutorial videos for learning {skill} in cybersecurity. Include video titles, URLs, creators, and brief descriptions.",
                    f"What are the most comprehensive {skill} video courses on YouTube for cybersecurity professionals?",
                ],
                "online_courses": [
                    f"Find online courses and certifications for {skill} in cybersecurity. Include course platforms, instructors, duration, and descriptions.",
                    f"What are the best {skill} courses on Coursera, edX, Udemy, and other platforms for cybersecurity?",
                ],
                "documentation": [
                    f"Find official documentation, guides, and technical resources for {skill} in cybersecurity. Include vendor docs and industry standards.",
                    f"What are the essential technical documentation and whitepapers for learning {skill}?",
                ],
                "tools": [
                    f"Find software tools, GitHub repositories, and hands-on platforms for practicing {skill} in cybersecurity.",
                    f"What are the best open-source tools and software for learning and implementing {skill}?",
                ],
                "books": [
                    f"Find the best books and ebooks for learning {skill} in cybersecurity. Include author, publisher, and brief description.",
                    f"What are the most recommended textbooks and reference books for {skill}?",
                ]
            }
        
        if resource_type == "all":
            # Return prompts for all types
            all_prompts = []
            for prompts in base_prompts.values():
                all_prompts.extend(prompts)
            return all_prompts
        else:
            return base_prompts.get(resource_type, [base_prompts["youtube_videos"][0]])
    
    async def _execute_search(self, prompt: str, skill: str, resource_type: str) -> List[DiscoveredResource]:
        """Execute a search using Perplexity API"""
        
        # Enhanced prompt for structured output
        enhanced_prompt = f"""
{prompt}

Please provide results in the following JSON format:
{{
    "resources": [
        {{
            "title": "Resource title",
            "url": "Full URL",
            "description": "Brief description",
            "author": "Creator/author name",
            "platform": "Platform/source",
            "duration_minutes": estimated_duration_in_minutes_or_null,
            "resource_type": "youtube_video|online_course|documentation|tool|book",
            "keywords": ["keyword1", "keyword2"]
        }}
    ]
}}

Focus on recent, high-quality resources with good educational value.
"""
        
        payload = {
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert educational resource curator specializing in cybersecurity. Provide accurate, up-to-date information about learning resources."
                },
                {
                    "role": "user", 
                    "content": enhanced_prompt
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.1,
            "top_p": 0.9,
            "search_domain_filter": ["youtube.com", "coursera.org", "edx.org", "udemy.com", "github.com"],
            "return_citations": True
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            return self._parse_search_results(content, skill)
            
        except Exception as e:
            logger.error(f"Perplexity API error: {e}")
            return []
    
    def _parse_search_results(self, content: str, skill: str) -> List[DiscoveredResource]:
        """Parse Perplexity response into DiscoveredResource objects"""
        resources = []
        
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                for item in data.get('resources', []):
                    try:
                        resource = DiscoveredResource(
                            title=item.get('title', ''),
                            url=item.get('url', ''),
                            description=item.get('description', ''),
                            resource_type=self._normalize_resource_type(item.get('resource_type', 'unknown')),
                            duration_estimate=item.get('duration_minutes'),
                            author=item.get('author'),
                            source_platform=self._extract_platform(item.get('url', '')),
                            keywords=item.get('keywords', []) + [skill],
                            raw_content=content
                        )
                        
                        if resource.url and resource.title:
                            resources.append(resource)
                            
                    except Exception as e:
                        logger.warning(f"Failed to parse resource item: {e}")
            
        except json.JSONDecodeError:
            # Fallback: try to extract resources using regex patterns
            logger.warning("JSON parsing failed, using regex fallback")
            resources = self._regex_parse_resources(content, skill)
        
        return resources
    
    def _normalize_resource_type(self, resource_type: str) -> str:
        """Normalize resource type to standard categories"""
        type_mapping = {
            'youtube_video': 'youtube_video',
            'video': 'youtube_video',
            'online_course': 'online_course', 
            'course': 'online_course',
            'documentation': 'documentation',
            'docs': 'documentation',
            'tool': 'tool',
            'software': 'tool',
            'book': 'book',
            'ebook': 'book',
            'article': 'article',
            'tutorial': 'tutorial'
        }
        
        return type_mapping.get(resource_type.lower(), 'article')
    
    def _extract_platform(self, url: str) -> str:
        """Extract platform name from URL"""
        if not url:
            return 'unknown'
        
        try:
            domain = urlparse(url).netloc.lower()
            if 'youtube.com' in domain or 'youtu.be' in domain:
                return 'youtube'
            elif 'coursera.org' in domain:
                return 'coursera'
            elif 'edx.org' in domain:
                return 'edx'
            elif 'udemy.com' in domain:
                return 'udemy'
            elif 'github.com' in domain:
                return 'github'
            elif 'medium.com' in domain:
                return 'medium'
            elif 'docs.' in domain:
                return 'documentation'
            else:
                return domain.replace('www.', '')
        except:
            return 'unknown'
    
    def _regex_parse_resources(self, content: str, skill: str) -> List[DiscoveredResource]:
        """Fallback regex parsing when JSON parsing fails"""
        resources = []
        
        # Look for URL patterns
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:!?]'
        urls = re.findall(url_pattern, content)
        
        # Try to extract titles near URLs
        for url in urls:
            try:
                # Look for text before the URL that might be a title
                url_index = content.find(url)
                if url_index > 0:
                    preceding_text = content[max(0, url_index-200):url_index]
                    # Extract potential title (look for quoted text or capitalized phrases)
                    title_patterns = [
                        r'"([^"]+)"',
                        r'([A-Z][a-zA-Z\s]+)',
                        r'([^\n.!?]+)(?=\s*' + re.escape(url) + ')'
                    ]
                    
                    title = "Educational Resource"
                    for pattern in title_patterns:
                        matches = re.findall(pattern, preceding_text)
                        if matches:
                            title = matches[-1].strip()
                            break
                    
                    resource = DiscoveredResource(
                        title=title,
                        url=url,
                        description=f"Educational resource for {skill}",
                        resource_type=self._guess_type_from_url(url),
                        source_platform=self._extract_platform(url),
                        keywords=[skill],
                        raw_content=content
                    )
                    resources.append(resource)
                    
            except Exception as e:
                logger.warning(f"Failed to parse URL {url}: {e}")
        
        return resources[:10]  # Limit to 10 resources from regex parsing
    
    def _guess_type_from_url(self, url: str) -> str:
        """Guess resource type from URL"""
        url_lower = url.lower()
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube_video'
        elif any(platform in url_lower for platform in ['coursera', 'edx', 'udemy']):
            return 'online_course'
        elif 'github.com' in url_lower:
            return 'tool'
        elif any(term in url_lower for term in ['docs', 'documentation', 'guide']):
            return 'documentation'
        else:
            return 'article'

class ContentScorer:
    """Score educational content quality using AI"""
    
    def __init__(self, ai_api_key: str, ai_provider: str = "anthropic"):
        self.ai_api_key = ai_api_key
        self.ai_provider = ai_provider
    
    async def score_resources(self, resources: List[DiscoveredResource], skill: str) -> List[Tuple[DiscoveredResource, float]]:
        """Score a list of resources for educational quality"""
        scored_resources = []
        
        for resource in resources:
            try:
                score = await self._score_single_resource(resource, skill)
                scored_resources.append((resource, score))
            except Exception as e:
                logger.error(f"Failed to score resource {resource.title}: {e}")
                # Assign default score if scoring fails
                scored_resources.append((resource, 0.5))
        
        return scored_resources
    
    async def _score_single_resource(self, resource: DiscoveredResource, skill: str) -> float:
        """Score a single resource for educational quality"""
        
        scoring_prompt = f"""
You are an expert educational content evaluator specializing in cybersecurity education.

Please evaluate this educational resource for learning "{skill}" and provide a quality score from 0.0 to 1.0.

Resource Details:
- Title: {resource.title}
- URL: {resource.url}
- Description: {resource.description}
- Resource Type: {resource.resource_type}
- Platform: {resource.source_platform}
- Author: {resource.author or 'Unknown'}

Evaluation Criteria:
1. Relevance to "{skill}" (25%)
2. Educational Quality & Comprehensiveness (25%)
3. Source Credibility & Authority (20%)
4. Content Recency & Up-to-date Information (15%)
5. Practical Application & Hands-on Learning (15%)

Please respond with ONLY a decimal number between 0.0 and 1.0 representing the quality score.
For example: 0.85

Consider:
- Is this directly relevant to learning {skill}?
- Does it provide comprehensive, practical education?
- Is the source credible (known platform, reputable author)?
- Is the content current and applicable?
- Does it offer hands-on learning opportunities?
"""
        
        if self.ai_provider == "anthropic":
            return await self._score_with_anthropic(scoring_prompt)
        elif self.ai_provider == "openai":
            return await self._score_with_openai(scoring_prompt)
        else:
            # Default scoring algorithm
            return self._basic_scoring(resource, skill)
    
    async def _score_with_anthropic(self, prompt: str) -> float:
        """Score using Anthropic/Claude API"""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.ai_api_key)
            
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            score_text = response.content[0].text.strip()
            return float(score_text)
            
        except Exception as e:
            logger.error(f"Anthropic scoring error: {e}")
            return 0.5
    
    async def _score_with_openai(self, prompt: str) -> float:
        """Score using OpenAI API"""
        try:
            import openai
            client = openai.OpenAI(api_key=self.ai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            score_text = response.choices[0].message.content.strip()
            return float(score_text)
            
        except Exception as e:
            logger.error(f"OpenAI scoring error: {e}")
            return 0.5
    
    def _basic_scoring(self, resource: DiscoveredResource, skill: str) -> float:
        """Basic scoring algorithm when AI APIs are unavailable"""
        score = 0.5  # Base score
        
        # Platform credibility
        credible_platforms = {
            'youtube': 0.7,
            'coursera': 0.9,
            'edx': 0.9, 
            'udemy': 0.8,
            'github': 0.8,
            'documentation': 0.9
        }
        platform_score = credible_platforms.get(resource.source_platform, 0.5)
        
        # Title relevance (simple keyword matching)
        skill_words = skill.lower().split()
        title_words = resource.title.lower().split()
        relevance = len([w for w in skill_words if any(w in tw for tw in title_words)]) / len(skill_words)
        
        # Resource type preference
        type_scores = {
            'online_course': 0.9,
            'tutorial': 0.8,
            'documentation': 0.8,
            'youtube_video': 0.7,
            'tool': 0.8,
            'article': 0.6
        }
        type_score = type_scores.get(resource.resource_type, 0.5)
        
        # Combine scores
        final_score = (platform_score * 0.4) + (relevance * 0.3) + (type_score * 0.3)
        return min(1.0, max(0.0, final_score))

class ResourceDiscoveryEngine:
    """Main resource discovery engine that orchestrates search and scoring"""
    
    def __init__(self):
        self.perplexity_api_key = config.get_api_key('perplexity')
        self.ai_api_key = config.get_api_key('anthropic') or config.get_api_key('openai')
        self.ai_provider = 'anthropic' if config.get_api_key('anthropic') else 'openai'
        
        if not self.perplexity_api_key:
            raise ValueError("Perplexity API key not found in configuration")
        
        self.searcher = PerplexitySearcher(self.perplexity_api_key)
        self.scorer = ContentScorer(self.ai_api_key, self.ai_provider) if self.ai_api_key else None
    
    async def discover_resources_for_skill(self, skill: str, resource_types: List[str] = None) -> List[Dict[str, Any]]:
        """Discover and score educational resources for a given skill"""
        
        if resource_types is None:
            resource_types = ["youtube_videos", "online_courses", "documentation", "tools"]
        
        logger.info(f"Starting resource discovery for skill: {skill}")
        
        all_resources = []
        
        # Search for each resource type
        for resource_type in resource_types:
            try:
                resources = await self.searcher.search_educational_content(skill, resource_type)
                logger.info(f"Found {len(resources)} {resource_type} resources for {skill}")
                all_resources.extend(resources)
            except Exception as e:
                logger.error(f"Failed to search for {resource_type}: {e}")
        
        # Score resources if AI API is available
        if self.scorer and all_resources:
            try:
                scored_resources = await self.scorer.score_resources(all_resources, skill)
                # Sort by score
                scored_resources.sort(key=lambda x: x[1], reverse=True)
                
                # Convert to output format
                result = []
                for resource, score in scored_resources:
                    result.append({
                        'title': resource.title,
                        'url': resource.url,
                        'description': resource.description,
                        'resource_type': resource.resource_type,
                        'source_platform': resource.source_platform,
                        'author': resource.author,
                        'duration_minutes': resource.duration_estimate,
                        'keywords': resource.keywords or [],
                        'quality_score': round(score, 3),
                        'discovered_at': datetime.now().isoformat()
                    })
                
                logger.info(f"Scored and ranked {len(result)} resources for {skill}")
                return result
                
            except Exception as e:
                logger.error(f"Failed to score resources: {e}")
        
        # Fallback: return unscored resources
        result = []
        for resource in all_resources:
            result.append({
                'title': resource.title,
                'url': resource.url,
                'description': resource.description,
                'resource_type': resource.resource_type,
                'source_platform': resource.source_platform,
                'author': resource.author,
                'duration_minutes': resource.duration_estimate,
                'keywords': resource.keywords or [],
                'quality_score': 0.5,  # Default score
                'discovered_at': datetime.now().isoformat()
            })
        
        logger.info(f"Returning {len(result)} unscored resources for {skill}")
        return result

# Initialize global discovery engine
discovery_engine = None

def get_discovery_engine():
    """Get or create the global resource discovery engine"""
    global discovery_engine
    if discovery_engine is None:
        try:
            discovery_engine = ResourceDiscoveryEngine()
        except Exception as e:
            logger.error(f"Failed to initialize discovery engine: {e}")
            return None
    return discovery_engine 