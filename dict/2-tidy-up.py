import json
from collections import defaultdict
from pprint import pprint

def handle_level(nest, level):
    nest_defs = []
    def_index = 0

    for definition, children in nest.items():
        def_index += 1

        if children:
            next_level = level + 1
            child_defs = handle_level(children, next_level)

            list_type = "li" if level == 1 else "number"
            content = definition if level == 1 else [{"tag": "span", "data": {"listType": "number"}, "content": f"{def_index}. "}, definition]

            nest_defs.append([{"tag": "div", "data": {"listType": list_type}, "content": content},
                              {"tag": "div", "data": {"listType": "ol"}, "content": child_defs}])
        else:
            nest_defs.append({"tag": "div", "data": {"listType": "li"}, "content": [{"tag": "span", "data": {"listType": "number"}, "content": f"{def_index}. "}, definition]})

    return nest_defs

def handle_nest(nested_gloss_obj, sense):
    nested_gloss = handle_level(nested_gloss_obj, 1)

    if nested_gloss:
        for entry in nested_gloss:
            sense["glosses"].append({"type": "structured-content", "content": entry})


blacklisted_tags = [
    'inflection-template',
    'table-tags',
    'nominative',
    'canonical',
    'class',
    'error-unknown-tag',
    'error-unrecognized-form',
    'infinitive',
    'includes-article',
    'obsolete',
    'archaic',
    'used-in-the-form'
]

unique_tags = []

line_count = 0
print_interval = 1000

lemma_dict = defaultdict(lambda: defaultdict(dict))
form_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
form_stuff = []
automated_forms = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

with open('data/kaikki/filename') as file:
    for line in file:
        line_count += 1
        if line_count % print_interval == 0:
            print(f"Processed {line_count} lines...")

        if line:
            data = json.loads(line)
            word, pos, senses, sounds, forms = data.get('word'), data.get('pos'), data.get('senses'), data.get('sounds', []), data.get('forms')

            if not (word and pos and senses):
                continue

            if forms:
                for form_data in forms:
                    form, tags = form_data.get('form'), form_data.get('tags')

                    if form and tags and not any(value in tags for value in blacklisted_tags):
                        for tag in tags:
                            if tag not in unique_tags:
                                unique_tags.append(tag)

                        automated_forms[form][word][pos].extend(tags)

            ipa = [{'ipa': sound['ipa'], 'tags': sound.get('tags', [])} for sound in sounds if sound and sound.get('ipa')]

            nested_gloss_obj = {}
            sense_index = 0

            for sense in senses:
                raw_glosses = sense.get('raw_glosses') or sense.get('glosses')
                form_of = sense.get('form_of')
                tags = sense.get('tags', [])

                glosses = raw_glosses or sense.get('glosses')

                if glosses and len(glosses) > 0:
                    if form_of:
                        form_stuff.append([word, sense, pos])
                    else:
                        if 'inflection of ' not in json.dumps(glosses):
                            lemma_dict[word][pos]['ipa'] = ipa
                            lemma_dict[word][pos]['senses'] = []

                            curr_sense = {'glosses': [], 'tags': tags}

                            if len(glosses) > 1:
                                nested_obj = nested_gloss_obj
                                for level in glosses:
                                    nested_obj[level] = nested_obj.get(level, {})
                                    nested_obj = nested_obj[level]

                                if sense_index == len(senses) - 1 and nested_gloss_obj:
                                    handle_nest(nested_gloss_obj, curr_sense)
                                    nested_gloss_obj = {}
                            elif len(glosses) == 1:
                                gloss = glosses[0]

                                if gloss not in json.dumps(curr_sense['glosses']):
                                    curr_sense['glosses'].append(gloss)

                            if curr_sense['glosses']:
                                lemma_dict[word][pos]['senses'].append(curr_sense)

                        if 'inflection of ' in json.dumps(glosses):
                            lemma = sense['glosses'][0].replace('.+(?=inflection of)', '').replace(' \\(.+?\\)', '').replace(':$', '').replace(':\\n.+', '').replace('inflection of ', '').replace(':.+', '').strip()
                            inflection = sense['glosses'][1]

                            if inflection and 'inflection of ' not in inflection and word != lemma:
                                form_dict[word][lemma][pos].append(inflection)

                sense_index += 1

print(f"Processed {line_count} lines...")

for form, info, pos in form_stuff:
    glosses = info['glosses']
    form_of = info['form_of'][0]['word']
    lemma = form_of[0]['word']

    if form != lemma:
        form_dict[form][lemma][pos].append(glosses[0] if not glosses[0].includes('##') else glosses[1])

missing_forms = 0

for form, info in automated_forms.items():
    if form not in form_dict:
        missing_forms += 1

        if len(info) < 5:
            for lemma, parts in info.items():
                for pos, glosses in parts.items():
                    if form != lemma:
                        form_dict[form][lemma][pos].extend([f"-automated- {gloss}" for gloss in glosses])

print(f"There were {missing_forms} missing forms that have now been automatically populated.")

with open(f"data/tidy/source_iso-target_iso-lemmas.json", "w") as f:
    json.dump(lemma_dict, f)

with open(f"data/tidy/source_iso-target_iso-forms.json", "w") as f:
    json.dump(form_dict, f)

print('2-tidy-up.py finished.')
