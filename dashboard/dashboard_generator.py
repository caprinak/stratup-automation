"""
Daily Dashboard Generator

Generates a beautiful, personalized dashboard HTML file
that can be used as browser start page.
"""

import json
import os
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import html
import yaml


@dataclass
class WidgetData:
    """Container for widget data."""
    type: str
    title: str
    content: Any
    icon: str = ""
    error: Optional[str] = None


class DashboardGenerator:
    """Generate personalized daily dashboard."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.output_path = Path("output/dashboard.html")
        self.cache_dir = Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self, path: str) -> Dict:
        """Load configuration from YAML file."""
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Expand environment variables in API keys
        if 'api_keys' in config:
            for key, value in config['api_keys'].items():
                if isinstance(value, str) and value.startswith('${'):
                    env_var = value[2:-1]
                    config['api_keys'][key] = os.environ.get(env_var, '')
        
        return config
    
    def generate(self) -> str:
        """Generate the complete dashboard HTML."""
        print("🎨 Generating dashboard...")
        
        # Collect all widget data
        widgets_data = self._collect_widget_data()
        
        # Generate HTML
        html_content = self._render_html(widgets_data)
        
        # Save to file
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Dashboard saved to: {self.output_path.absolute()}")
        return str(self.output_path.absolute())
    
    def _collect_widget_data(self) -> Dict[str, WidgetData]:
        """Collect data for all configured widgets."""
        data = {}
        
        # Always include these
        data['greeting'] = self._get_greeting_data()
        data['datetime'] = self._get_datetime_data()
        
        # Configured widgets
        for widget in self.config.get('layout', {}).get('widgets', []):
            widget_type = widget.get('type')
            
            try:
                if widget_type == 'weather':
                    data['weather'] = self._get_weather_data()
                elif widget_type == 'quote':
                    data['quote'] = self._get_quote_data()
                elif widget_type == 'tasks':
                    data['tasks'] = self._get_tasks_data()
                elif widget_type == 'calendar':
                    data['calendar'] = self._get_calendar_data()
                elif widget_type == 'stats':
                    data['stats'] = self._get_stats_data()
                elif widget_type == 'news':
                    data['news'] = self._get_news_data()
                elif widget_type == 'github':
                    data['github'] = self._get_github_data()
            except Exception as e:
                print(f"⚠️ Error fetching {widget_type}: {e}")
                data[widget_type] = WidgetData(
                    type=widget_type,
                    title=widget_type.title(),
                    content=None,
                    error=str(e)
                )
        
        # Bookmarks
        data['bookmarks'] = self.config.get('bookmarks', [])
        
        return data
    
    def _get_greeting_data(self) -> WidgetData:
        """Generate greeting based on time of day."""
        hour = datetime.now().hour
        name = self.config.get('user', {}).get('name', 'there')
        
        if hour < 6:
            greeting = "Good night"
            emoji = "🌙"
        elif hour < 12:
            greeting = "Good morning"
            emoji = "☀️"
        elif hour < 17:
            greeting = "Good afternoon"
            emoji = "🌤️"
        elif hour < 21:
            greeting = "Good evening"
            emoji = "🌆"
        else:
            greeting = "Good night"
            emoji = "🌙"
        
        return WidgetData(
            type='greeting',
            title='Greeting',
            content={
                'text': f"{greeting}, {name}!",
                'emoji': emoji
            },
            icon=emoji
        )
    
    def _get_datetime_data(self) -> WidgetData:
        """Get current date/time data."""
        now = datetime.now()
        
        return WidgetData(
            type='datetime',
            title='Date & Time',
            content={
                'date': now.strftime("%A, %B %d, %Y"),
                'time': now.strftime("%H:%M:%S"),
                'timestamp': now.isoformat()
            },
            icon='🕐'
        )
    
    def _get_weather_data(self) -> WidgetData:
        """Fetch weather data from API."""
        weather_config = self.config.get('weather', {})
        location = weather_config.get('location', 'auto')
        units = weather_config.get('units', 'metric')
        
        try:
            # Using wttr.in (free, no API key required)
            if location == 'auto':
                url = f"https://wttr.in/?format=j1"
            else:
                url = f"https://wttr.in/{urllib.parse.quote(location)}?format=j1"
            
            # Check cache first
            cache_file = self.cache_dir / "weather.json"
            if self._is_cache_valid(cache_file, minutes=30):
                with open(cache_file, 'r') as f:
                    data = json.load(f)
            else:
                with urllib.request.urlopen(url, timeout=10) as response:
                    data = json.loads(response.read())
                
                # Save to cache
                with open(cache_file, 'w') as f:
                    json.dump(data, f)
            
            current = data['current_condition'][0]
            
            # Get weather icon
            code = int(current['weatherCode'])
            icon = self._weather_code_to_icon(code)
            
            # Temperature based on units
            if units == 'metric':
                temp = current['temp_C']
                feels = current['FeelsLikeC']
                temp_unit = '°C'
            else:
                temp = current['temp_F']
                feels = current['FeelsLikeF']
                temp_unit = '°F'
            
            return WidgetData(
                type='weather',
                title='Weather',
                content={
                    'temperature': f"{temp}{temp_unit}",
                    'feels_like': f"{feels}{temp_unit}",
                    'description': current['weatherDesc'][0]['value'],
                    'humidity': f"{current['humidity']}%",
                    'wind': f"{current['windspeedKmph']} km/h",
                    'icon': icon,
                    'location': data.get('nearest_area', [{}])[0].get('areaName', [{}])[0].get('value', 'Unknown')
                },
                icon=icon
            )
            
        except Exception as e:
            return WidgetData(
                type='weather',
                title='Weather',
                content=None,
                icon='🌡️',
                error=str(e)
            )
    
    def _weather_code_to_icon(self, code: int) -> str:
        """Convert weather code to emoji icon."""
        if code == 113:
            return "☀️"
        elif code in [116]:
            return "⛅"
        elif code in [119, 122]:
            return "☁️"
        elif code in [143, 248, 260]:
            return "🌫️"
        elif code in [176, 263, 266, 293, 296, 299, 302, 305, 308, 353, 356, 359]:
            return "🌧️"
        elif code in [179, 182, 185, 281, 284, 311, 314, 317, 350, 362, 365, 374, 377]:
            return "🌨️"
        elif code in [200, 386, 389, 392, 395]:
            return "⛈️"
        elif code in [227, 230, 320, 323, 326, 329, 332, 335, 338, 368, 371]:
            return "❄️"
        else:
            return "🌡️"
    
    def _get_quote_data(self) -> WidgetData:
        """Fetch inspirational quote."""
        try:
            # Check daily cache
            cache_file = self.cache_dir / f"quote_{datetime.now().strftime('%Y-%m-%d')}.json"
            
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    data = json.load(f)
            else:
                # Fetch new quote
                url = "https://api.quotable.io/random?tags=technology|success|motivational"
                with urllib.request.urlopen(url, timeout=10) as response:
                    data = json.loads(response.read())
                
                with open(cache_file, 'w') as f:
                    json.dump(data, f)
            
            return WidgetData(
                type='quote',
                title='Quote',
                content={
                    'text': data['content'],
                    'author': data['author']
                },
                icon='💡'
            )
            
        except Exception as e:
            # Fallback quote
            return WidgetData(
                type='quote',
                title='Quote',
                content={
                    'text': "The best way to predict the future is to create it.",
                    'author': "Peter Drucker"
                },
                icon='💡'
            )
    
    def _get_tasks_data(self) -> WidgetData:
        """Fetch tasks from configured source."""
        source = self.config.get('layout', {}).get('widgets', [])
        task_widget = next((w for w in source if w.get('type') == 'tasks'), {})
        task_source = task_widget.get('source', 'local')
        
        try:
            if task_source == 'todoist':
                return self._get_todoist_tasks()
            else:
                return self._get_local_tasks()
        except Exception as e:
            return WidgetData(
                type='tasks',
                title='Tasks',
                content=[],
                icon='📋',
                error=str(e)
            )
    
    def _get_todoist_tasks(self) -> WidgetData:
        """Fetch tasks from Todoist API."""
        api_key = self.config.get('api_keys', {}).get('todoist', '')
        
        if not api_key:
            return self._get_local_tasks()
        
        url = "https://api.todoist.com/rest/v2/tasks?filter=today"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            tasks = json.loads(response.read())
        
        return WidgetData(
            type='tasks',
            title='Today\'s Tasks',
            content=[
                {
                    'id': task['id'],
                    'content': task['content'],
                    'priority': task['priority'],
                    'completed': False,
                    'due': task.get('due', {}).get('string', '')
                }
                for task in tasks[:5]
            ],
            icon='📋'
        )
    
    def _get_local_tasks(self) -> WidgetData:
        """Get tasks from local file."""
        tasks_file = Path("data/tasks.json")
        
        if tasks_file.exists():
            with open(tasks_file, 'r') as f:
                tasks = json.load(f)
        else:
            tasks = [
                {"id": 1, "content": "Add your tasks here", "completed": False},
                {"id": 2, "content": "Edit data/tasks.json", "completed": False},
            ]
        
        return WidgetData(
            type='tasks',
            title='Tasks',
            content=tasks[:5],
            icon='📋'
        )
    
    def _get_calendar_data(self) -> WidgetData:
        """Get calendar events."""
        # For now, using local events
        # TODO: Integrate with Google Calendar API
        
        events_file = Path("data/events.json")
        
        if events_file.exists():
            with open(events_file, 'r') as f:
                events = json.load(f)
        else:
            # Sample events
            now = datetime.now()
            events = [
                {
                    "time": "10:00",
                    "title": "Team Standup",
                    "duration": 30,
                    "type": "meeting"
                },
                {
                    "time": "14:00",
                    "title": "Design Review",
                    "duration": 60,
                    "type": "meeting"
                },
                {
                    "time": "16:00",
                    "title": "1:1 with Manager",
                    "duration": 30,
                    "type": "meeting"
                }
            ]
        
        return WidgetData(
            type='calendar',
            title='Today\'s Schedule',
            content=events[:5],
            icon='📅'
        )
    
    def _get_stats_data(self) -> WidgetData:
        """Get gamification stats."""
        stats_file = Path("data/gamification.json")
        
        if stats_file.exists():
            with open(stats_file, 'r') as f:
                stats = json.load(f)
        else:
            stats = {
                'current_streak': 0,
                'longest_streak': 0,
                'total_points': 0,
                'level': 1,
                'total_startups': 0
            }
        
        # Determine level name
        levels = [
            (0, "Newbie", "🌱"),
            (100, "Apprentice", "📚"),
            (300, "Intermediate", "⚙️"),
            (600, "Advanced", "🔧"),
            (1000, "Expert", "💎"),
            (2000, "Master", "🏅"),
            (5000, "Grandmaster", "👑"),
        ]
        
        level_name = "Newbie"
        level_icon = "🌱"
        for threshold, name, icon in levels:
            if stats.get('total_points', 0) >= threshold:
                level_name = name
                level_icon = icon
        
        return WidgetData(
            type='stats',
            title='Your Stats',
            content={
                'streak': stats.get('current_streak', 0),
                'longest_streak': stats.get('longest_streak', 0),
                'points': stats.get('total_points', 0),
                'level': stats.get('level', 1),
                'level_name': level_name,
                'level_icon': level_icon,
                'total_startups': stats.get('total_startups', 0)
            },
            icon='🎯'
        )
    
    def _get_news_data(self) -> WidgetData:
        """Fetch tech news from Hacker News."""
        try:
            cache_file = self.cache_dir / "news.json"
            
            if self._is_cache_valid(cache_file, minutes=15):
                with open(cache_file, 'r') as f:
                    stories = json.load(f)
            else:
                # Fetch top stories from HN
                url = "https://hacker-news.firebaseio.com/v0/topstories.json"
                with urllib.request.urlopen(url, timeout=10) as response:
                    story_ids = json.loads(response.read())[:5]
                
                stories = []
                for story_id in story_ids:
                    story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                    with urllib.request.urlopen(story_url, timeout=5) as response:
                        story = json.loads(response.read())
                        stories.append({
                            'title': story.get('title', ''),
                            'url': story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                            'score': story.get('score', 0),
                            'comments': story.get('descendants', 0)
                        })
                
                with open(cache_file, 'w') as f:
                    json.dump(stories, f)
            
            return WidgetData(
                type='news',
                title='Tech News',
                content=stories,
                icon='📰'
            )
            
        except Exception as e:
            return WidgetData(
                type='news',
                title='Tech News',
                content=[],
                icon='📰',
                error=str(e)
            )
    
    def _get_github_data(self) -> WidgetData:
        """Fetch GitHub notifications and stats."""
        token = self.config.get('api_keys', {}).get('github', '')
        
        if not token:
            return WidgetData(
                type='github',
                title='GitHub',
                content={'notifications': 0, 'error': 'No token configured'},
                icon='🐙'
            )
        
        try:
            # Get notifications count
            req = urllib.request.Request(
                "https://api.github.com/notifications",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                notifications = json.loads(response.read())
            
            return WidgetData(
                type='github',
                title='GitHub',
                content={
                    'notifications': len(notifications),
                    'unread': [
                        {
                            'repo': n['repository']['full_name'],
                            'title': n['subject']['title'],
                            'type': n['subject']['type']
                        }
                        for n in notifications[:3]
                    ]
                },
                icon='🐙'
            )
            
        except Exception as e:
            return WidgetData(
                type='github',
                title='GitHub',
                content={'notifications': 0},
                icon='🐙',
                error=str(e)
            )
    
    def _is_cache_valid(self, cache_file: Path, minutes: int) -> bool:
        """Check if cache file is still valid."""
        if not cache_file.exists():
            return False
        
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        return datetime.now() - mtime < timedelta(minutes=minutes)
    
    def _render_html(self, data: Dict[str, Any]) -> str:
        """Render the complete dashboard HTML."""
        
        theme = self.config.get('theme', {})
        user = self.config.get('user', {})
        bookmarks = data.get('bookmarks', [])
        search_config = self.config.get('search', {})
        
        # Generate bookmark links HTML
        bookmarks_html = self._render_bookmarks(bookmarks)
        
        # Generate widgets HTML
        tasks_html = self._render_tasks(data.get('tasks'))
        calendar_html = self._render_calendar(data.get('calendar'))
        stats_html = self._render_stats(data.get('stats'))
        news_html = self._render_news(data.get('news'))
        github_html = self._render_github(data.get('github'))
        
        # Weather data
        weather = data.get('weather')
        weather_html = ""
        if weather and weather.content:
            w = weather.content
            weather_html = f'''
            <div class="weather-widget">
                <span class="weather-icon">{w['icon']}</span>
                <div class="weather-info">
                    <span class="weather-temp">{w['temperature']}</span>
                    <span class="weather-desc">{w['description']}</span>
                </div>
            </div>
            '''
        
        # Quote data
        quote = data.get('quote')
        quote_html = ""
        if quote and quote.content:
            quote_html = f'''
            <div class="quote-widget">
                <p class="quote-text">"{html.escape(quote.content['text'])}"</p>
                <p class="quote-author">— {html.escape(quote.content['author'])}</p>
            </div>
            '''
        
        # Greeting
        greeting = data.get('greeting')
        greeting_text = greeting.content['text'] if greeting else "Hello!"
        greeting_emoji = greeting.content['emoji'] if greeting else "👋"
        
        # Date/time
        dt = data.get('datetime')
        date_str = dt.content['date'] if dt else datetime.now().strftime("%A, %B %d, %Y")
        
        # Search box
        search_html = ""
        if search_config.get('enabled', True):
            engine = search_config.get('engine', 'google')
            search_urls = {
                'google': 'https://google.com/search',
                'duckduckgo': 'https://duckduckgo.com/',
                'bing': 'https://bing.com/search'
            }
            search_html = f'''
            <form class="search-form" action="{search_urls.get(engine, search_urls['google'])}" method="get">
                <input type="text" name="q" class="search-input" 
                       placeholder="{search_config.get('placeholder', 'Search...')}"
                       autocomplete="off">
                <button type="submit" class="search-button">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"></circle>
                        <path d="m21 21-4.35-4.35"></path>
                    </svg>
                </button>
            </form>
            '''
        
        # Background style
        bg = theme.get('background', {})
        bg_type = bg.get('type', 'gradient')
        bg_value = bg.get('value', 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)')
        
        if bg_type == 'gradient':
            bg_style = f"background: {bg_value};"
        elif bg_type == 'solid':
            bg_style = f"background-color: {bg_value};"
        elif bg_type == 'image':
            bg_style = f"background: url('{bg_value}') center/cover fixed;"
        elif bg_type == 'unsplash':
            bg_style = f"background: url('https://source.unsplash.com/1920x1080/?{bg_value}') center/cover fixed;"
        else:
            bg_style = f"background: {bg_value};"
        
        accent = theme.get('accent_color', '#6366f1')
        
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - {date_str}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --accent: {accent};
            --accent-light: {accent}33;
            --bg-card: rgba(255, 255, 255, 0.05);
            --bg-card-hover: rgba(255, 255, 255, 0.08);
            --text-primary: #ffffff;
            --text-secondary: rgba(255, 255, 255, 0.7);
            --text-muted: rgba(255, 255, 255, 0.5);
            --border: rgba(255, 255, 255, 0.1);
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --radius: 16px;
            --radius-sm: 8px;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            {bg_style}
            min-height: 100vh;
            color: var(--text-primary);
            padding: 40px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        /* Header Section */
        .header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        
        .greeting {{
            font-size: 2.5rem;
            font-weight: 300;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
        }}
        
        .greeting-emoji {{
            font-size: 2.5rem;
        }}
        
        .date {{
            font-size: 1.1rem;
            color: var(--text-secondary);
            margin-bottom: 24px;
        }}
        
        .clock {{
            font-size: 5rem;
            font-weight: 200;
            letter-spacing: -2px;
            margin: 20px 0;
            font-variant-numeric: tabular-nums;
        }}
        
        .clock-seconds {{
            font-size: 2.5rem;
            opacity: 0.5;
        }}
        
        /* Weather Widget */
        .weather-widget {{
            display: inline-flex;
            align-items: center;
            gap: 12px;
            background: var(--bg-card);
            padding: 12px 24px;
            border-radius: 50px;
            margin: 20px 0;
        }}
        
        .weather-icon {{
            font-size: 2rem;
        }}
        
        .weather-info {{
            display: flex;
            flex-direction: column;
            align-items: flex-start;
        }}
        
        .weather-temp {{
            font-size: 1.5rem;
            font-weight: 600;
        }}
        
        .weather-desc {{
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}
        
        /* Search */
        .search-form {{
            max-width: 600px;
            margin: 30px auto;
            position: relative;
        }}
        
        .search-input {{
            width: 100%;
            padding: 16px 24px;
            padding-right: 56px;
            font-size: 1rem;
            border: 2px solid var(--border);
            border-radius: 50px;
            background: var(--bg-card);
            color: var(--text-primary);
            outline: none;
            transition: all 0.3s ease;
        }}
        
        .search-input:focus {{
            border-color: var(--accent);
            background: var(--bg-card-hover);
        }}
        
        .search-input::placeholder {{
            color: var(--text-muted);
        }}
        
        .search-button {{
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            width: 40px;
            height: 40px;
            border: none;
            border-radius: 50%;
            background: var(--accent);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }}
        
        .search-button:hover {{
            transform: translateY(-50%) scale(1.05);
        }}
        
        /* Quote */
        .quote-widget {{
            max-width: 700px;
            margin: 30px auto;
            padding: 24px 32px;
            background: var(--bg-card);
            border-radius: var(--radius);
            border-left: 4px solid var(--accent);
        }}
        
        .quote-text {{
            font-size: 1.1rem;
            font-style: italic;
            color: var(--text-primary);
            margin-bottom: 12px;
        }}
        
        .quote-author {{
            font-size: 0.9rem;
            color: var(--text-secondary);
            text-align: right;
        }}
        
        /* Grid Layout */
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 24px;
            margin-top: 40px;
        }}
        
        /* Cards */
        .card {{
            background: var(--bg-card);
            border-radius: var(--radius);
            padding: 24px;
            backdrop-filter: blur(10px);
            border: 1px solid var(--border);
            transition: all 0.3s ease;
        }}
        
        .card:hover {{
            background: var(--bg-card-hover);
            transform: translateY(-2px);
        }}
        
        .card-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }}
        
        .card-icon {{
            font-size: 1.2rem;
        }}
        
        .card-title {{
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-secondary);
            font-weight: 600;
        }}
        
        /* Tasks */
        .task-list {{
            list-style: none;
        }}
        
        .task-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 0;
            border-bottom: 1px solid var(--border);
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .task-item:last-child {{
            border-bottom: none;
        }}
        
        .task-item:hover {{
            padding-left: 8px;
        }}
        
        .task-checkbox {{
            width: 20px;
            height: 20px;
            border: 2px solid var(--border);
            border-radius: 50%;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .task-checkbox:hover {{
            border-color: var(--accent);
        }}
        
        .task-checkbox.completed {{
            background: var(--accent);
            border-color: var(--accent);
        }}
        
        .task-checkbox.completed::after {{
            content: "✓";
            color: white;
            font-size: 12px;
        }}
        
        .task-content {{
            flex: 1;
        }}
        
        .task-content.completed {{
            text-decoration: line-through;
            opacity: 0.5;
        }}
        
        .task-priority {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }}
        
        .task-priority.p1 {{ background: #ef4444; }}
        .task-priority.p2 {{ background: #f97316; }}
        .task-priority.p3 {{ background: #3b82f6; }}
        .task-priority.p4 {{ background: #6b7280; }}
        
        /* Calendar Events */
        .event-item {{
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 12px 0;
            border-bottom: 1px solid var(--border);
        }}
        
        .event-item:last-child {{
            border-bottom: none;
        }}
        
        .event-time {{
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--accent);
            background: var(--accent-light);
            padding: 4px 10px;
            border-radius: var(--radius-sm);
            white-space: nowrap;
        }}
        
        .event-details {{
            flex: 1;
        }}
        
        .event-title {{
            font-weight: 500;
        }}
        
        .event-duration {{
            font-size: 0.8rem;
            color: var(--text-muted);
        }}
        
        /* Stats Widget */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 16px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: var(--radius-sm);
        }}
        
        .stat-icon {{
            font-size: 1.5rem;
            margin-bottom: 8px;
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--accent);
        }}
        
        .stat-label {{
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        /* Quick Links */
        .links-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
            gap: 12px;
        }}
        
        .link-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            padding: 16px 12px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: var(--radius-sm);
            text-decoration: none;
            color: var(--text-primary);
            transition: all 0.3s ease;
        }}
        
        .link-item:hover {{
            background: var(--accent-light);
            transform: translateY(-4px);
        }}
        
        .link-icon {{
            width: 40px;
            height: 40px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }}
        
        .link-name {{
            font-size: 0.8rem;
            font-weight: 500;
        }}
        
        /* News */
        .news-item {{
            padding: 12px 0;
            border-bottom: 1px solid var(--border);
        }}
        
        .news-item:last-child {{
            border-bottom: none;
        }}
        
        .news-link {{
            color: var(--text-primary);
            text-decoration: none;
            display: block;
        }}
        
        .news-link:hover {{
            color: var(--accent);
        }}
        
        .news-title {{
            font-weight: 500;
            margin-bottom: 4px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        
        .news-meta {{
            font-size: 0.8rem;
            color: var(--text-muted);
        }}
        
        /* GitHub */
        .github-notifications {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
        }}
        
        .github-count {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--accent);
        }}
        
        .github-label {{
            font-size: 0.9rem;
            color: var(--text-secondary);
        }}
        
        .github-item {{
            padding: 8px 0;
            font-size: 0.85rem;
            border-bottom: 1px solid var(--border);
        }}
        
        .github-item:last-child {{
            border-bottom: none;
        }}
        
        .github-repo {{
            color: var(--accent);
            font-weight: 500;
        }}
        
        /* Pomodoro */
        .pomodoro-timer {{
            text-align: center;
            padding: 20px 0;
        }}
        
        .pomodoro-time {{
            font-size: 4rem;
            font-weight: 200;
            font-variant-numeric: tabular-nums;
            margin-bottom: 20px;
        }}
        
        .pomodoro-controls {{
            display: flex;
            justify-content: center;
            gap: 12px;
        }}
        
        .pomodoro-btn {{
            padding: 12px 24px;
            border: none;
            border-radius: var(--radius-sm);
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .pomodoro-btn.primary {{
            background: var(--accent);
            color: white;
        }}
        
        .pomodoro-btn.secondary {{
            background: var(--bg-card);
            color: var(--text-primary);
            border: 1px solid var(--border);
        }}
        
        .pomodoro-btn:hover {{
            transform: scale(1.05);
        }}
        
        .pomodoro-status {{
            margin-top: 16px;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}
        
        /* Notes Widget */
        .notes-textarea {{
            width: 100%;
            min-height: 150px;
            padding: 16px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            color: var(--text-primary);
            font-family: inherit;
            font-size: 0.9rem;
            resize: vertical;
            outline: none;
        }}
        
        .notes-textarea:focus {{
            border-color: var(--accent);
        }}
        
        .notes-textarea::placeholder {{
            color: var(--text-muted);
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            body {{
                padding: 20px;
            }}
            
            .greeting {{
                font-size: 1.8rem;
            }}
            
            .clock {{
                font-size: 3rem;
            }}
            
            .grid {{
                grid-template-columns: 1fr;
            }}
        }}
        
        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .card {{
            animation: fadeIn 0.5s ease forwards;
        }}
        
        .card:nth-child(1) {{ animation-delay: 0.1s; }}
        .card:nth-child(2) {{ animation-delay: 0.2s; }}
        .card:nth-child(3) {{ animation-delay: 0.3s; }}
        .card:nth-child(4) {{ animation-delay: 0.4s; }}
        .card:nth-child(5) {{ animation-delay: 0.5s; }}
        .card:nth-child(6) {{ animation-delay: 0.6s; }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header Section -->
        <header class="header">
            <div class="greeting">
                <span>{greeting_text}</span>
                <span class="greeting-emoji">{greeting_emoji}</span>
            </div>
            <div class="date">{date_str}</div>
            
            <div class="clock" id="clock">
                <span id="clock-time">00:00</span><span class="clock-seconds" id="clock-seconds">:00</span>
            </div>
            
            {weather_html}
            
            {search_html}
            
            {quote_html}
        </header>
        
        <!-- Main Grid -->
        <div class="grid">
            {tasks_html}
            {calendar_html}
            {stats_html}
            
            <!-- Pomodoro Timer -->
            <div class="card">
                <div class="card-header">
                    <span class="card-icon">🍅</span>
                    <span class="card-title">Pomodoro Timer</span>
                </div>
                <div class="pomodoro-timer">
                    <div class="pomodoro-time" id="pomodoro-time">25:00</div>
                    <div class="pomodoro-controls">
                        <button class="pomodoro-btn primary" id="pomodoro-start">Start</button>
                        <button class="pomodoro-btn secondary" id="pomodoro-reset">Reset</button>
                    </div>
                    <div class="pomodoro-status" id="pomodoro-status">Ready to focus</div>
                </div>
            </div>
            
            <!-- Quick Links -->
            <div class="card">
                <div class="card-header">
                    <span class="card-icon">🔗</span>
                    <span class="card-title">Quick Links</span>
                </div>
                <div class="links-grid">
                    {bookmarks_html}
                </div>
            </div>
            
            {news_html}
            {github_html}
            
            <!-- Notes -->
            <div class="card">
                <div class="card-header">
                    <span class="card-icon">📝</span>
                    <span class="card-title">Quick Notes</span>
                </div>
                <textarea class="notes-textarea" id="notes" 
                          placeholder="Write your thoughts here..."
                          oninput="saveNotes(this.value)"></textarea>
            </div>
        </div>
    </div>
    
    <script>
        // ============================================
        // LIVE CLOCK
        // ============================================
        function updateClock() {{
            const now = new Date();
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const seconds = String(now.getSeconds()).padStart(2, '0');
            
            document.getElementById('clock-time').textContent = `${{hours}}:${{minutes}}`;
            document.getElementById('clock-seconds').textContent = `:${{seconds}}`;
        }}
        
        setInterval(updateClock, 1000);
        updateClock();
        
        // ============================================
        // POMODORO TIMER
        // ============================================
        let pomodoroTime = 25 * 60; // 25 minutes in seconds
        let pomodoroInterval = null;
        let pomodoroRunning = false;
        
        function formatTime(seconds) {{
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return `${{String(mins).padStart(2, '0')}}:${{String(secs).padStart(2, '0')}}`;
        }}
        
        function updatePomodoroDisplay() {{
            document.getElementById('pomodoro-time').textContent = formatTime(pomodoroTime);
        }}
        
        function startPomodoro() {{
            if (pomodoroRunning) {{
                // Pause
                clearInterval(pomodoroInterval);
                pomodoroRunning = false;
                document.getElementById('pomodoro-start').textContent = 'Resume';
                document.getElementById('pomodoro-status').textContent = 'Paused';
            }} else {{
                // Start
                pomodoroRunning = true;
                document.getElementById('pomodoro-start').textContent = 'Pause';
                document.getElementById('pomodoro-status').textContent = 'Focus time! 🎯';
                
                pomodoroInterval = setInterval(() => {{
                    pomodoroTime--;
                    updatePomodoroDisplay();
                    
                    if (pomodoroTime <= 0) {{
                        clearInterval(pomodoroInterval);
                        pomodoroRunning = false;
                        document.getElementById('pomodoro-start').textContent = 'Start';
                        document.getElementById('pomodoro-status').textContent = '🎉 Time for a break!';
                        
                        // Notification
                        if (Notification.permission === 'granted') {{
                            new Notification('🍅 Pomodoro Complete!', {{
                                body: 'Time for a 5-minute break!',
                                icon: '🍅'
                            }});
                        }}
                        
                        // Play sound
                        try {{
                            const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2telezsJNJDc77JzOR8wpu');
                            audio.play();
                        }} catch(e) {{}}
                    }}
                }}, 1000);
            }}
        }}
        
        function resetPomodoro() {{
            clearInterval(pomodoroInterval);
            pomodoroTime = 25 * 60;
            pomodoroRunning = false;
            updatePomodoroDisplay();
            document.getElementById('pomodoro-start').textContent = 'Start';
            document.getElementById('pomodoro-status').textContent = 'Ready to focus';
        }}
        
        document.getElementById('pomodoro-start').addEventListener('click', startPomodoro);
        document.getElementById('pomodoro-reset').addEventListener('click', resetPomodoro);
        
        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {{
            Notification.requestPermission();
        }}
        
        // ============================================
        // TASK MANAGEMENT
        // ============================================
        function toggleTask(element) {{
            const checkbox = element.querySelector('.task-checkbox');
            const content = element.querySelector('.task-content');
            
            checkbox.classList.toggle('completed');
            content.classList.toggle('completed');
            
            // Save to localStorage
            const taskId = element.dataset.taskId;
            let completedTasks = JSON.parse(localStorage.getItem('completedTasks') || '[]');
            
            if (checkbox.classList.contains('completed')) {{
                completedTasks.push(taskId);
            }} else {{
                completedTasks = completedTasks.filter(id => id !== taskId);
            }}
            
            localStorage.setItem('completedTasks', JSON.stringify(completedTasks));
        }}
        
        // Restore completed tasks
        document.addEventListener('DOMContentLoaded', () => {{
            const completedTasks = JSON.parse(localStorage.getItem('completedTasks') || '[]');
            completedTasks.forEach(taskId => {{
                const taskElement = document.querySelector(`[data-task-id="${{taskId}}"]`);
                if (taskElement) {{
                    taskElement.querySelector('.task-checkbox').classList.add('completed');
                    taskElement.querySelector('.task-content').classList.add('completed');
                }}
            }});
        }});
        
        // ============================================
        // NOTES
        // ============================================
        function saveNotes(value) {{
            localStorage.setItem('dashboard-notes', value);
        }}
        
        // Load saved notes
        document.addEventListener('DOMContentLoaded', () => {{
            const savedNotes = localStorage.getItem('dashboard-notes');
            if (savedNotes) {{
                document.getElementById('notes').value = savedNotes;
            }}
        }});
        
        // ============================================
        // SEARCH SHORTCUTS
        // ============================================
        const searchShortcuts = {{
            'g': 'https://google.com/search?q=',
            'yt': 'https://youtube.com/results?search_query=',
            'gh': 'https://github.com/search?q=',
            'r': 'https://reddit.com/search?q=',
            'w': 'https://en.wikipedia.org/wiki/'
        }};
        
        const searchForm = document.querySelector('.search-form');
        if (searchForm) {{
            searchForm.addEventListener('submit', function(e) {{
                const input = this.querySelector('input');
                const query = input.value.trim();
                
                // Check for shortcut prefix
                for (const [prefix, url] of Object.entries(searchShortcuts)) {{
                    if (query.startsWith(prefix + ' ')) {{
                        e.preventDefault();
                        const searchQuery = query.slice(prefix.length + 1);
                        window.location.href = url + encodeURIComponent(searchQuery);
                        return;
                    }}
                }}
            }});
        }}
        
        // ============================================
        // KEYBOARD SHORTCUTS
        // ============================================
        document.addEventListener('keydown', (e) => {{
            // Focus search on '/' key
            if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {{
                e.preventDefault();
                document.querySelector('.search-input')?.focus();
            }}
            
            // Start/pause pomodoro on 'p' key
            if (e.key === 'p' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {{
                e.preventDefault();
                startPomodoro();
            }}
        }});
        
        // ============================================
        // AUTO-REFRESH DATA
        // ============================================
        // Refresh page every 30 minutes to get fresh data
        setTimeout(() => {{
            window.location.reload();
        }}, 30 * 60 * 1000);
    </script>
</body>
</html>'''
        
        return html_content
    
    def _render_bookmarks(self, bookmarks: List[Dict]) -> str:
        """Render bookmarks HTML."""
        icons_map = {
            'github': '🐙',
            'mail': '📧',
            'calendar': '📅',
            'book': '📚',
            'message-circle': '💬',
            'youtube': '▶️',
            'twitter': '🐦',
            'figma': '🎨',
        }
        
        html = ""
        for bookmark in bookmarks:
            icon = icons_map.get(bookmark.get('icon', ''), '🔗')
            color = bookmark.get('color', '#6366f1')
            
            html += f'''
            <a href="{html.escape(bookmark['url'])}" class="link-item" target="_blank">
                <div class="link-icon" style="background: {color}20; color: {color};">
                    {icon}
                </div>
                <span class="link-name">{html.escape(bookmark['name'])}</span>
            </a>
            '''
        
        return html
    
    def _render_tasks(self, tasks_data: Optional[WidgetData]) -> str:
        """Render tasks widget HTML."""
        if not tasks_data or not tasks_data.content:
            return ""
        
        tasks_html = ""
        for task in tasks_data.content:
            priority_class = f"p{task.get('priority', 4)}"
            completed_class = "completed" if task.get('completed') else ""
            
            tasks_html += f'''
            <li class="task-item" data-task-id="{task.get('id', '')}" onclick="toggleTask(this)">
                <div class="task-checkbox {completed_class}"></div>
                <span class="task-content {completed_class}">{html.escape(str(task.get('content', '')))}</span>
                <span class="task-priority {priority_class}"></span>
            </li>
            '''
        
        return f'''
        <div class="card">
            <div class="card-header">
                <span class="card-icon">📋</span>
                <span class="card-title">{tasks_data.title}</span>
            </div>
            <ul class="task-list">
                {tasks_html}
            </ul>
        </div>
        '''
    
    def _render_calendar(self, calendar_data: Optional[WidgetData]) -> str:
        """Render calendar widget HTML."""
        if not calendar_data or not calendar_data.content:
            return ""
        
        events_html = ""
        for event in calendar_data.content:
            events_html += f'''
            <div class="event-item">
                <span class="event-time">{html.escape(str(event.get('time', '')))}</span>
                <div class="event-details">
                    <div class="event-title">{html.escape(str(event.get('title', '')))}</div>
                    <div class="event-duration">{event.get('duration', 30)} minutes</div>
                </div>
            </div>
            '''
        
        return f'''
        <div class="card">
            <div class="card-header">
                <span class="card-icon">📅</span>
                <span class="card-title">{calendar_data.title}</span>
            </div>
            {events_html}
        </div>
        '''
    
    def _render_stats(self, stats_data: Optional[WidgetData]) -> str:
        """Render stats widget HTML."""
        if not stats_data or not stats_data.content:
            return ""
        
        s = stats_data.content
        
        return f'''
        <div class="card">
            <div class="card-header">
                <span class="card-icon">🎯</span>
                <span class="card-title">Your Stats</span>
            </div>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-icon">🔥</div>
                    <div class="stat-value">{s.get('streak', 0)}</div>
                    <div class="stat-label">Day Streak</div>
                </div>
                <div class="stat-item">
                    <div class="stat-icon">{s.get('level_icon', '⭐')}</div>
                    <div class="stat-value">{s.get('level', 1)}</div>
                    <div class="stat-label">{s.get('level_name', 'Level')}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-icon">⭐</div>
                    <div class="stat-value">{s.get('points', 0)}</div>
                    <div class="stat-label">Points</div>
                </div>
                <div class="stat-item">
                    <div class="stat-icon">🚀</div>
                    <div class="stat-value">{s.get('total_startups', 0)}</div>
                    <div class="stat-label">Startups</div>
                </div>
            </div>
        </div>
        '''
    
    def _render_news(self, news_data: Optional[WidgetData]) -> str:
        """Render news widget HTML."""
        if not news_data or not news_data.content:
            return ""
        
        news_html = ""
        for item in news_data.content:
            news_html += f'''
            <div class="news-item">
                <a href="{html.escape(item.get('url', '#'))}" class="news-link" target="_blank">
                    <div class="news-title">{html.escape(item.get('title', ''))}</div>
                    <div class="news-meta">⬆️ {item.get('score', 0)} · 💬 {item.get('comments', 0)}</div>
                </a>
            </div>
            '''
        
        return f'''
        <div class="card">
            <div class="card-header">
                <span class="card-icon">📰</span>
                <span class="card-title">{news_data.title}</span>
            </div>
            {news_html}
        </div>
        '''
    
    def _render_github(self, github_data: Optional[WidgetData]) -> str:
        """Render GitHub widget HTML."""
        if not github_data or not github_data.content:
            return ""
        
        g = github_data.content
        notifications = g.get('notifications', 0)
        
        unread_html = ""
        for item in g.get('unread', []):
            unread_html += f'''
            <div class="github-item">
                <span class="github-repo">{html.escape(item.get('repo', ''))}</span>
                <br>
                <small>{html.escape(item.get('title', '')[:50])}</small>
            </div>
            '''
        
        return f'''
        <div class="card">
            <div class="card-header">
                <span class="card-icon">🐙</span>
                <span class="card-title">GitHub</span>
            </div>
            <div class="github-notifications">
                <span class="github-count">{notifications}</span>
                <span class="github-label">notifications</span>
            </div>
            {unread_html}
        </div>
        '''


# ============================================
# MAIN ENTRY POINT
# ============================================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Daily Dashboard")
    parser.add_argument("--config", "-c", default="config.yaml", help="Config file path")
    parser.add_argument("--output", "-o", default="output/dashboard.html", help="Output file path")
    parser.add_argument("--open", "-O", action="store_true", help="Open in browser after generating")
    
    args = parser.parse_args()
    
    generator = DashboardGenerator(config_path=args.config)
    generator.output_path = Path(args.output)
    
    output_file = generator.generate()
    
    if args.open:
        import webbrowser
        webbrowser.open(f"file:///{output_file}")
