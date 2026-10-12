"""Validate the mod's resources before shipping.

Checks: every JSON parses; datapack folders are 1.21 names; every lightning_sword:<id>
reference resolves to a registered id or an existing model file; lang key sets match;
every "translate" key and every Text.translatable() key exists in both languages.

Exit 0 = clean, 1 = problems found.  Usage: python tools/validate_resources.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, 'src', 'main', 'resources')
JAVA = os.path.join(ROOT, 'src', 'main', 'java')
NS = 'lightning_sword'
problems = []


def fail(msg):
    problems.append(msg)
    print('  FAIL  %s' % msg)


def java_sources():
    for root, _d, files in os.walk(JAVA):
        for f in files:
            if f.endswith('.java'):
                yield os.path.join(root, f)


def resource_files(suffix=None):
    for root, _d, files in os.walk(RES):
        for f in sorted(files):
            if suffix is None or f.endswith(suffix):
                yield os.path.join(root, f)


# ---- ids the mod registers in Java -----------------------------------------
registered = set()
for p in java_sources():
    registered |= set(re.findall(r'id\("([a-z0-9_]+)"\)', open(p, encoding='utf-8').read()))
print('registered ids: %s' % sorted(registered))

# ---- every JSON parses ------------------------------------------------------
njson = 0
for p in resource_files('.json'):
    njson += 1
    try:
        json.load(open(p, encoding='utf-8'))
    except Exception as exc:
        fail('%s -> %s' % (os.path.relpath(p, RES), exc))
print('json parsed: %d' % njson)

# ---- datapack folder names -------------------------------------------------
VALID_DIRS = {'advancement', 'recipe', 'loot_table', 'tags', 'worldgen', 'damage_type',
              'enchantment', 'trim_pattern', 'trim_material', 'jukebox_song',
              'painting_variant', 'banner_pattern'}
data = os.path.join(RES, 'data')
if os.path.isdir(data):
    for ns_dir in sorted(os.listdir(data)):
        inner = os.path.join(data, ns_dir)
        if os.path.isdir(inner):
            for kind in sorted(os.listdir(inner)):
                if os.path.isdir(os.path.join(inner, kind)) and kind not in VALID_DIRS:
                    fail('data/%s/%s is not a valid 1.21 datapack folder' % (ns_dir, kind))

# ---- lightning_sword:<id> references ---------------------------------------
for p in resource_files():
    try:
        text = open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    for ref in sorted(set(re.findall(r'%s:[a-z0-9_/]+' % NS, text))):
        path = ref.split(':', 1)[1]
        if path.startswith('item/'):
            model = os.path.join(RES, 'assets', NS, 'models', path + '.json')
            if not os.path.isfile(model):
                fail('%s (in %s) has no models/%s.json' % (ref, os.path.relpath(p, RES), path))
        elif not path.startswith('models/') and path not in registered:
            fail('%s (in %s) is not registered by the mod' % (ref, os.path.relpath(p, RES)))

# ---- lang ------------------------------------------------------------------
lang = {}
for loc in ('en_us', 'zh_cn'):
    p = os.path.join(RES, 'assets', NS, 'lang', loc + '.json')
    lang[loc] = json.load(open(p, encoding='utf-8')) if os.path.isfile(p) else {}
    if not lang[loc]:
        fail('missing or empty lang file: %s.json' % loc)
if set(lang['en_us']) != set(lang['zh_cn']):
    fail('lang key sets differ: only-en %s / only-zh %s'
         % (sorted(set(lang['en_us']) - set(lang['zh_cn'])),
            sorted(set(lang['zh_cn']) - set(lang['en_us']))))

json_translate = set()
for p in resource_files('.json'):
    if os.sep + 'lang' + os.sep in p:
        continue
    json_translate |= set(re.findall(r'"translate"\s*:\s*"([^"]+)"', open(p, encoding='utf-8').read()))
for key in sorted(json_translate):
    for loc in lang:
        if key not in lang[loc]:
            fail('"translate": "%s" missing from %s.json' % (key, loc))

used = set()
for p in java_sources():
    used |= set(re.findall(r'Text\.translatable\("([^"]+)"', open(p, encoding='utf-8').read()))
for key in sorted(used):
    if key not in lang['en_us']:
        fail('Text.translatable("%s") missing from lang' % key)

print('lang: en=%d zh=%d, translate-in-json=%d, used-in-java=%d'
      % (len(lang['en_us']), len(lang['zh_cn']), len(json_translate), len(used)))
unused = sorted(k for k in lang['en_us']
                if k not in used and k not in json_translate and not k.startswith('itemGroup.'))
if unused:
    print('  note: lang keys used by neither Java nor JSON: %s' % unused)

print()
if problems:
    print('PROBLEMS: %d' % len(problems))
    sys.exit(1)
print('all resource checks passed')
