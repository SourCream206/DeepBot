# discord_bot.py
import discord
from discord.ext import commands
import sqlite3
from pathlib import Path
import os
from dotenv import load_dotenv
import sys
from typing import List, Tuple

load_dotenv()

token = os.getenv('DISCORD_TOKEN')


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "items.db"


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='S', intents=intents)

def search_items_single(query: str) -> List[Tuple]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT name, category, subcategories, rarity, voi
        FROM items
        WHERE name LIKE ? 
           OR subcategories LIKE ? 
           OR category LIKE ?
        ORDER BY 
            CASE rarity 
                WHEN 'relic' THEN 1
                WHEN 'legendary' THEN 2
                WHEN 'named' THEN 3
                WHEN 'hallowtide' THEN 4
                WHEN 'normal' THEN 5
                ELSE 6
            END,
            name
        LIMIT 30
    """, (f"%{query}%", f"%{query}%", f"%{query}%"))
    
    results = cur.fetchall()
    conn.close()
    return results

def search_items_multi(tags: List[str]) -> List[Tuple]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    conditions = []
    params = []
    
    for tag in tags:
        conditions.append("""
            (name LIKE ? OR subcategories LIKE ? OR category LIKE ?)
        """)
        params.extend([f"%{tag}%", f"%{tag}%", f"%{tag}%"])
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
        SELECT name, category, subcategories, rarity, voi
        FROM items
        WHERE {where_clause}
        ORDER BY 
            CASE rarity 
                WHEN 'relic' THEN 1
                WHEN 'legendary' THEN 2
                WHEN 'named' THEN 3
                WHEN 'hallowtide' THEN 4
                WHEN 'normal' THEN 5
                ELSE 6
            END,
            name
        LIMIT 30
    """
    
    cur.execute(query, params)
    results = cur.fetchall()
    conn.close()
    return results

def search_items_any(tags: List[str]) -> List[Tuple]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    conditions = []
    params = []
    
    for tag in tags:
        conditions.append("""
            (name LIKE ? OR subcategories LIKE ? OR category LIKE ?)
        """)
        params.extend([f"%{tag}%", f"%{tag}%", f"%{tag}%"])
    
    where_clause = " OR ".join(conditions)
    
    query = f"""
        SELECT name, category, subcategories, rarity, voi
        FROM items
        WHERE {where_clause}
        ORDER BY 
            CASE rarity 
                WHEN 'relic' THEN 1
                WHEN 'legendary' THEN 2
                WHEN 'named' THEN 3
                WHEN 'hallowtide' THEN 4
                WHEN 'normal' THEN 5
                ELSE 6
            END,
            name
        LIMIT 30
    """
    
    cur.execute(query, params)
    results = cur.fetchall()
    conn.close()
    return results

def smart_search(query: str) -> List[Tuple]:
    """Smart search with filters like rarity:legendary, voi:yes, etc."""
    # Parse advanced filters
    filters = {
        'name_terms': [],
        'rarity': None,
        'category': None,
        'voi': None,
        'subcategory': None,
        'exact_phrases': []
    }
    
    # Split query into parts
    parts = []
    current_part = []
    in_quotes = False
    
    # Parse quoted phrases
    for char in query:
        if char == '"':
            in_quotes = not in_quotes
        elif char == ' ' and not in_quotes:
            if current_part:
                parts.append(''.join(current_part))
                current_part = []
        else:
            current_part.append(char)
    
    if current_part:
        parts.append(''.join(current_part))
    
    # Process each part
    for part in parts:
        part_lower = part.lower()
        
        if ':' in part:
            # It's a filter
            key, value = part.split(':', 1)
            key = key.strip().lower()
            value = value.strip().lower()
            
            if key == 'rarity':
                filters['rarity'] = value
            elif key in ['type', 'category']:
                filters['category'] = value
            elif key == 'voi':
                filters['voi'] = 1 if value in ['yes', 'true', '1'] else 0
            elif key in ['sub', 'subcategory']:
                filters['subcategory'] = value
        elif part.startswith('"') and part.endswith('"'):
            # Exact phrase
            filters['exact_phrases'].append(part[1:-1])
        else:
            # Regular search term
            filters['name_terms'].append(part)
    
    # Build SQL query based on filters
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    conditions = []
    params = []
    
    # Handle name terms (OR between them)
    if filters['name_terms']:
        term_conditions = []
        for term in filters['name_terms']:
            term_conditions.append("(name LIKE ? OR subcategories LIKE ?)")
            params.extend([f"%{term}%", f"%{term}%"])
        conditions.append(f"({' OR '.join(term_conditions)})")
    
    # Handle exact phrases
    if filters['exact_phrases']:
        phrase_conditions = []
        for phrase in filters['exact_phrases']:
            phrase_conditions.append("(name LIKE ? OR subcategories LIKE ?)")
            params.extend([f"%{phrase}%", f"%{phrase}%"])
        if phrase_conditions:
            if conditions:
                conditions.append("AND")
            conditions.append(f"({' OR '.join(phrase_conditions)})")
    
    # Handle filters
    if filters['rarity']:
        conditions.append("LOWER(rarity) = ?")
        params.append(filters['rarity'])
    
    if filters['category']:
        conditions.append("LOWER(category) LIKE ?")
        params.append(f"%{filters['category']}%")
    
    if filters['voi'] is not None:
        conditions.append("voi = ?")
        params.append(filters['voi'])
    
    if filters['subcategory']:
        conditions.append("LOWER(subcategories) LIKE ?")
        params.append(f"%{filters['subcategory']}%")
    
    # Build final query
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query_sql = f"""
        SELECT name, category, subcategories, rarity, voi
        FROM items
        WHERE {where_clause}
        ORDER BY 
            CASE rarity 
                WHEN 'relic' THEN 1
                WHEN 'legendary' THEN 2
                WHEN 'named' THEN 3
                WHEN 'hallowtide' THEN 4
                WHEN 'normal' THEN 5
                ELSE 6
            END,
            name
        LIMIT 30
    """
    
    cur.execute(query_sql, params)
    results = cur.fetchall()
    conn.close()
    return results, filters

@bot.event
async def on_ready():
    print(f'{bot.user} is called by the deep!')
    await bot.change_presence(activity=discord.Game(name="Shelp for commands"))

@bot.command(name='item', help='Search for items with advanced filters')
async def item_search(ctx, *, query):
    """
    Search for items with multiple tags and filters:
    
    BASIC SEARCH:
    Sitem sword              - Single term search
    Sitem sword + flame      - Items with BOTH sword AND flame (AND search)
    Sitem sword,flame        - Items with EITHER sword OR flame (OR search)
    Sitem sword/flame        - Same as comma (OR search)
    Sitem light dagger       - Space separated (OR search)
    
    ADVANCED FILTERS:
    Sitem rarity:legendary           - Filter by rarity
    Sitem type:weapon                - Filter by category
    Sitem voi:yes                    - Only VOI items
    Sitem sub:elemental              - Filter by subcategory
    Sitem "light dagger"             - Exact phrase search
    
    COMBINED SEARCH:
    Sitem sword rarity:legendary type:weapon  - Multiple filters
    Sitem "hero's blade" rarity:legendary     - Phrase with filter
    Sitem sword + flame voi:yes               - AND search with filter
    """
    if not query or len(query.strip()) < 2:
        await ctx.send("Please provide at least 2 characters to search for.")
        return
    
    query = query.strip()
    
    # Check if query contains advanced filters (has colon or quotes)
    has_filters = any(':' in part or (part.startswith('"') and part.endswith('"')) 
                     for part in query.split())
    
    if has_filters:
        # Use smart search with filters
        results, filters = smart_search(query)
        search_type = "SMART"
        tags = []
    elif '+' in query:
        # AND search
        tags = [tag.strip() for tag in query.split('+') if tag.strip()]
        search_type = "AND"
        results = search_items_multi(tags)
    elif ',' in query or '/' in query:
        # OR search
        tags = [tag.strip() for tag in query.replace('/', ',').split(',') if tag.strip()]
        search_type = "OR"
        results = search_items_any(tags)
    elif ' ' in query:
        # Space-separated OR search
        tags = [tag.strip() for tag in query.split() if tag.strip()]
        search_type = "OR"
        results = search_items_any(tags)
    else:
        # Single term search
        tags = [query]
        search_type = "SINGLE"
        results = search_items_single(query)
    
    if not results:
        if search_type == "AND":
            await ctx.send(f"No items found matching ALL tags: `{'`, `'.join(tags)}`")
        elif search_type == "OR":
            await ctx.send(f"No items found matching ANY tag: `{'`, `'.join(tags)}`")
        elif search_type == "SMART":
            # Build descriptive message
            filter_msgs = []
            if filters['name_terms']:
                filter_msgs.append(f"terms: `{'`, `'.join(filters['name_terms'])}`")
            if filters['exact_phrases']:
                filter_msgs.append(f"phrases: `{'`, `'.join(filters['exact_phrases'])}`")
            if filters['rarity']:
                filter_msgs.append(f"rarity: `{filters['rarity']}`")
            if filters['category']:
                filter_msgs.append(f"type: `{filters['category']}`")
            if filters['voi'] is not None:
                filter_msgs.append(f"VOI: `{'yes' if filters['voi'] else 'no'}`")
            if filters['subcategory']:
                filter_msgs.append(f"subcategory: `{filters['subcategory']}`")
            
            await ctx.send(f"No items found with filters: {', '.join(filter_msgs)}")
        else:
            await ctx.send(f"No items found for: `{query}`")
        return
    
    # Create embed title and description
    if search_type == "SMART":
        # Build title for smart search
        filter_parts = []
        if filters['name_terms']:
            filter_parts.append(f"terms: `{'`, `'.join(filters['name_terms'])}`")
        if filters['exact_phrases']:
            filter_parts.append(f"phrases: `{'`, `'.join(filters['exact_phrases'])}`")
        if filters['rarity']:
            filter_parts.append(f"rarity: `{filters['rarity']}`")
        if filters['category']:
            filter_parts.append(f"type: `{filters['category']}`")
        if filters['voi'] is not None:
            filter_parts.append(f"VOI: `{'yes' if filters['voi'] else 'no'}`")
        if filters['subcategory']:
            filter_parts.append(f"sub: `{filters['subcategory']}`")
        
        title = "Smart Search Results"
        if filter_parts:
            title = f"Items with: {', '.join(filter_parts)}"
    else:
        title_map = {
            "AND": f"Items with ALL tags: `{'`, `'.join(tags)}`",
            "OR": f"Items with ANY tag: `{'`, `'.join(tags)}`",
            "SINGLE": f"Items matching: `{query}`"
        }
        title = title_map.get(search_type, f"Search: `{query}`")
    
    embed = discord.Embed(
        title=title[:256],  # Discord title limit
        description=f"Found {len(results)} item(s)",
        color=discord.Color.blue()
    )
    
    # Add filter info for smart search
    if search_type == "SMART" and (filters['rarity'] or filters['category'] or filters['voi'] is not None or filters['subcategory']):
        filter_info = []
        if filters['rarity']:
            filter_info.append(f"**Rarity:** `{filters['rarity']}`")
        if filters['category']:
            filter_info.append(f"**Type:** `{filters['category']}`")
        if filters['voi'] is not None:
            filter_info.append(f"**VOI:** `{'yes' if filters['voi'] else 'no'}`")
        if filters['subcategory']:
            filter_info.append(f"**Subcategory:** `{filters['subcategory']}`")
        
        if filter_info:
            embed.add_field(name="Active Filters", value="\n".join(filter_info), inline=False)
    
    # Add results to embed
    for name, cat, sub, rarity, voi in results:
        voi_tag = " <:VOI:1470243357065220187>" if voi else ""
        rarity_colors = {
            'relic': '🟣',
            'legendary': '🟡',
            'named': '🔵',
            'hallowtide': '🟠',
            'normal': '⚪'
        }
        rarity_emoji = rarity_colors.get(rarity.lower(), '⚪')
        
        # Highlight matching terms in the name
        display_name = name
        if search_type != "SMART":
            for tag in tags:
                if tag.lower() in name.lower():
                    display_name = f"**{name}**"
                    break
        
        embed.add_field(
            name=f"{rarity_emoji} {display_name}",
            value=f"**Type:** {cat}\n**Subcategories:** {sub}\n**Rarity:** {rarity}{voi_tag}",
            inline=True
        )
    
    # Split if too many results
    if len(embed.fields) > 10:
        embeds = []
        for i in range(0, len(results), 10):
            page_embed = discord.Embed(
                title=f"{title[:240]} (Page {i//10 + 1})",
                color=discord.Color.blue()
            )
            for name, cat, sub, rarity, voi in results[i:i+10]:
                voi_tag = " <:VOI:1470243357065220187>" if voi else ""
                page_embed.add_field(
                    name=f"{name}",
                    value=f"Type: {cat}\nSub: {sub}\nRarity: {rarity}{voi_tag}",
                    inline=True
                )
            embeds.append(page_embed)
        
        for page_embed in embeds:
            await ctx.send(embed=page_embed)
    else:
        await ctx.send(embed=embed)

@bot.command(name='random', help='Get a random item')
async def random_item(ctx):
    """Get a random item from database"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT name, category, subcategories, rarity, voi
        FROM items
        ORDER BY RANDOM()
        LIMIT 1
    """)
    
    result = cur.fetchone()
    conn.close()
    
    if result:
        name, cat, sub, rarity, voi = result
        voi_tag = " <:VOI:1470243357065220187>" if voi else ""
        
        embed = discord.Embed(
            title="🎲 Random Item",
            color=discord.Color.green()
        )
        embed.add_field(name="Name", value=name, inline=False)
        embed.add_field(name="Category", value=cat, inline=True)
        embed.add_field(name="Subcategories", value=sub, inline=True)
        embed.add_field(name="Rarity", value=f"{rarity}{voi_tag}", inline=True)
        
        await ctx.send(embed=embed)

@bot.command(name='helpme', help='Show all available commands')
async def help_command(ctx):
    """Custom help command"""
    embed = discord.Embed(
        title="📖 Item Lookup Bot Help",
        description="Commands for searching items from the database",
        color=discord.Color.blue()
    )
    
    commands_list = [
        ("Sitem <query>", "**Advanced search with all features:**\n"
                         "**Basic:** `Sitem sword`, `Sitem light dagger`\n"
                         "**AND:** `Sitem sword+flame` (both terms)\n"
                         "**OR:** `Sitem sword,flame` (either term)\n"
                         "**Filters:** `Sitem rarity:legendary`\n"
                         "           `Sitem type:weapon voi:yes`\n"
                         "           `Sitem sub:elemental`\n"
                         "**Exact:** `Sitem \"light dagger\"`"),
        ("Srandom", "Get a random item"),
        ("Shelp", "Show this help message"),
        ("Sexamples", "Show search examples")
    ]
    
    for cmd, desc in commands_list:
        embed.add_field(name=cmd, value=desc, inline=False)
    
    embed.set_footer(text="Prefix: S | Use + for AND, comma/space for OR, : for filters")
    
    await ctx.send(embed=embed)

@bot.command(name='examples', help='Show search examples')
async def examples_command(ctx):
    """Show search examples"""
    embed = discord.Embed(
        title="🔍 Search Examples",
        description="How to use the Sitem command:",
        color=discord.Color.gold()
    )
    
    examples = [
        ("Basic Search", "`Sitem sword` - Find items with 'sword'"),
        ("Multi-term OR", "`Sitem light dagger` - Items with 'light' OR 'dagger'"),
        ("AND Search", "`Sitem sword+flame` - Items with BOTH 'sword' AND 'flame'"),
        ("OR Search", "`Sitem sword,flame` - Items with EITHER 'sword' OR 'flame'"),
        ("", "`Sitem sword/flame` - Same as comma (OR search)"),
        ("Exact Phrase", "`Sitem \"light dagger\"` - Exact phrase match"),
        ("Rarity Filter", "`Sitem rarity:legendary` - Only legendary items"),
        ("Type Filter", "`Sitem type:weapon` - Only weapons"),
        ("VOI Filter", "`Sitem voi:yes` - Only VOI items"),
        ("Subcategory Filter", "`Sitem sub:elemental` - Items with 'elemental' in subcategories"),
        ("Combined Filters", "`Sitem sword rarity:legendary type:weapon` - All conditions"),
        ("Mixed Search", "`Sitem sword+flame voi:yes` - AND search with VOI filter"),
        ("Random Item", "`Srandom` - Get a random item")
    ]
    
    for title, example in examples:
        if title:
            embed.add_field(name=title, value=example, inline=False)
        else:
            embed.add_field(name="\u200b", value=example, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='voi', help='Show all VOI items')
async def voi_items(ctx):
    """Show all VOI items"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT name, category, subcategories, rarity, voi
        FROM items
        WHERE voi = 1
        ORDER BY 
            CASE rarity 
                WHEN 'relic' THEN 1
                WHEN 'legendary' THEN 2
                WHEN 'named' THEN 3
                WHEN 'hallowtide' THEN 4
                WHEN 'normal' THEN 5
                ELSE 6
            END,
            name
    """)
    
    results = cur.fetchall()
    conn.close()
    
    if not results:
        await ctx.send("No VOI items found.")
        return
    
    # Create embed
    embed = discord.Embed(
        title="<:VOI:1470243357065220187> VOI Items",
        description=f"Found {len(results)} VOI item(s)",
        color=discord.Color.gold()
    )
    
    # Add results in chunks
    for i, (name, cat, sub, rarity, voi) in enumerate(results[:20], 1):
        rarity_colors = {
            'relic': '🟣',
            'legendary': '🟡',
            'named': '🔵',
            'hallowtide': '🟠',
            'normal': '⚪'
        }
        rarity_emoji = rarity_colors.get(rarity.lower(), '⚪')
        
        embed.add_field(
            name=f"{i}. {rarity_emoji} {name}",
            value=f"Type: {cat}\nRarity: {rarity}",
            inline=True
        )
    
    if len(results) > 20:
        embed.set_footer(text=f"Showing 20 of {len(results)} VOI items")
    
    await ctx.send(embed=embed)

# Run the bot
if __name__ == "__main__":
    try:
        print("🚀 Starting bot...")
        bot.run(token)
    except Exception as e:
        print(f"Error: {e}")