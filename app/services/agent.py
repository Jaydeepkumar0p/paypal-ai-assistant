"""The agent loop: ask the model, run the tools it picks, send results back, repeat."""
import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.services.tools import make_tools
from app.utils.llm import llm
from app.services.catalog import CATEGORIES

MAX_STEPS = 6

SYSTEM_PROMPT = '''You are PayPilot, a sharp, friendly shopping assistant inside an online electronics store.
Store categories: ''' + ', '.join(CATEGORIES) + '''.
How to work:
- Use tools for every fact about products, prices, stock, the cart or orders. Never invent them. Prices are in USD. Some products have no rating yet, so never make one up.
- To find or recommend, call find_products with filters the shopper implies: under $60 means max_price 60, cheapest means sort price_asc, best rated means sort rating, deals means on_sale true, well rated means min_rating 4.3. Use category only when it matches a store category.
- To compare, call compare_products. For a budget plus several needs, call build_bundle. For details, call get_product.
- Recommend like an expert: give the reason in one short line (rating, price, a standout feature) and mention a sale or low stock when it matters.
- When asked to add or buy something (this, it, the first one, the cheapest), call add_to_cart with the right product ids. The ids of earlier results are written at the end of earlier assistant messages under Products shown. Several products can go in one call.
- You can NOT pay or place orders. When the shopper wants to pay or check out, make sure the cart is right, call open_cart with target checkout, and tell them to finish with the PayPal button there.
- If a search finds nothing, say so and try again with fewer filters or suggest the closest alternative.
- Keep replies to 1-3 short sentences. The app shows product cards and tables itself, so do not list every field.
'''


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return ''.join(p.get('text', '') if isinstance(p, dict) else str(p) for p in content)
    return str(content or '')


def to_messages(history):
    return [(HumanMessage if m['role'] == 'user' else AIMessage)(content=m['content']) for m in history]


def shown_note(ui):
    '''Remember which products were shown, so "add the second one" works next turn.'''
    items = ui.get('products') or []
    if not items:
        return ''
    return '\n(Products shown: ' + '; '.join(p['id'] + ' ' + p['name'] + ' $' + p['price'] for p in items[:8]) + ')'


async def run_agent(session, message):
    ui = {'products': None, 'compare': None, 'bundle': None, 'filters': None, 'navigate': None}
    tools = make_tools(session, ui)
    tool_map = {t.name: t for t in tools}
    model = llm.bind_tools(tools)

    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    messages += to_messages(session['history'][-12:])
    messages.append(HumanMessage(content=message))

    reply = 'Sorry, I got stuck. Could you try again?'
    for _ in range(MAX_STEPS):
        try:
            ai = await model.ainvoke(messages)
        except Exception as e:
            print('LLM error:', repr(e))
            reply = 'Sorry, the AI service had a problem (' + type(e).__name__ + '). Please try again.'
            break
        messages.append(ai)
        if not ai.tool_calls:
            reply = text_of(ai.content)
            break
        for call in ai.tool_calls:
            fn = tool_map.get(call['name'])
            result = await fn.ainvoke(call['args']) if fn else json.dumps({'error': 'Unknown tool'})
            messages.append(ToolMessage(content=str(result), tool_call_id=call['id']))

    session['history'] += [
        {'role': 'user', 'content': message},
        {'role': 'assistant', 'content': reply + shown_note(ui)},
    ]
    session['history'] = session['history'][-20:]
    return {'reply': reply, **ui}
