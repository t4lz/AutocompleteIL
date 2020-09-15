import pandas as pd
import re
from difflib import SequenceMatcher

# to suppress SettingWithCopyWarning
pd.options.mode.chained_assignment = None


def similar(a, b):
    return SequenceMatcher(None, a, b).real_quick_ratio()


def read_streets_csv(path: str):
    return pd.read_csv(path, header=1, true_values='official',
                       encoding='iso8859_8', skipinitialspace=True,
                       converters={
                           # needed cause values have trailing whitespace
                           'region_name': str.strip,
                           'city_name': str.strip,
                           'street_name': str.strip,
                           'street_name_status': str.strip
                       })


def read_cities_pop(path: str):
    column_names = ['city_code', 'city_name', 'region_code', 'region_name',
                    'lishkat_mana_code', 'lishkat_mana', 'moaza_ezorit_code',
                    'moaza_ezorit', 'total_pop', 'pop_0_6', 'pop_6_18',
                    'pop_19_45', 'pop_46_55', 'pop_56_64', 'pop_65_plus']
    ct = pd.read_csv('data/cities_pop.csv', header=0, encoding='iso8859_8',
                     skipinitialspace=True, names=column_names,
                     converters={'city_name': str.strip})
    return ct


def get_cities(st_df: pd.DataFrame):
    return st_df[['city_code', 'city_name', 'region_code', 'region_name']] \
        .drop_duplicates().sort_values('city_name').reset_index(drop=True)


def get_streets_with_pop():
    st = read_streets_csv('data/streets.csv')
    # join to itself on city_code+street_code, to add official name
    st = st.join(st[['city_code', 'street_code', 'street_name']].set_index(['city_code', 'street_code']), on=['city_code', 'official_code'], rsuffix='_official')
    st['city_street_code'] = st['city_code'].astype(str) + '_' + st['street_code'].astype(str)
    st['city_street_code_official'] = st['city_code'].astype(str) + '_' + st['official_code'].astype(str)
    st['is_official_name'] = (st['street_name_status'] == 'official')
    st.drop('street_name_status', axis=1, inplace=True)
    cities_pop = get_cities_pop()[['city_code', 'pop_score', 'not_tlv']]
    cities_pop.set_index('city_code', inplace=True)
    st = st.join(cities_pop, on='city_code')
    st['official_factor'] = st['is_official_name'] * 0.01 + 1       # 1 if False, 1.01 if true
    return st.sort_values(by='not_tlv').drop('not_tlv', axis=1)


def get_cities_pop():
    cities_pop = read_cities_pop('data/cities_pop.csv')
    cities_pop['pop_19_64'] = cities_pop['pop_19_45'] + cities_pop['pop_46_55'] + cities_pop['pop_56_64']
    cities_pop['pop_score'] = cities_pop['pop_19_64'] / cities_pop['pop_19_64'].sum()
    cities_pop['not_tlv'] = abs(cities_pop['region_code'] - 51)
    return cities_pop[['city_code', 'city_name', 'total_pop', 'pop_19_64', 'pop_score', 'not_tlv']].sort_values(by='not_tlv')


streets = get_streets_with_pop()
cities = get_cities_pop()

word_re = '(?:[^\W\d_]|-|\'|")+'

# examples:
# שפינוזה 5, תל אביב
# שפינוזה, תל אביב
# ברוך שפינוזה, תל-אביב
full_address_re = re.compile('(?P<street>{word}(?:\s{word})*)(?P<num>\s+\d+)?,\s*(?P<city>{word}(?:\s{word})*)?'.format(word=word_re), re.UNICODE)


# example:
# שפינוזה, תל אביב - יפו 5
# meant to catch number typed after choosing auto complete suggestion
number_after_formatted_address_re = re.compile(
    '(?P<street>{word}(?:\s{word})*),\s*(?P<city>{word}(?:\s{word})*)\s*(?P<num>\d+)'.format(word=word_re), re.UNICODE)

# examples:
# שפינוזה 5 תל אביב
# שבטי ישראל 17 רמת השרון
address_no_comma_re = re.compile('(?P<street>{word}(?:\s{word})*)\s+(?P<num>\d+)\s+(?P<city>{word}(?:\s{word})*)'.format(word=word_re), re.UNICODE)

# examples:
# שפינוזה 5
street_with_num_re = re.compile('(?P<street>{word}(?:\s{word})*)\s+(?P<num>\d+)'.format(word=word_re), re.UNICODE)

def dict_with_possible_cities(d: dict, found_cities: list):
    return [dict(d, **{'city_input': d['city'], 'city': found_city}) for found_city in found_cities]


# return list with a dict for each possible match for dict's city
# {'a': 1, 'city': 'ramat'} -> [{'a': 1, 'city_input': 'ramat', city: 'ramat gan'},
#                               {'a': 1, 'city_input': 'ramat', city: 'ramat hasharon'}, ... ]
# if city is emtpy ('', None, ...) returned list only contains one dict with city ''
# if there are no possible cities - return empty list
def fix_dict_with_cities(d: dict):
    return [dict(d, **{'city_input': (d['city'] if d['city'] else ''), 'city': found_city}) for found_city in get_matching_cities(d['city'])]


# return a list of all possible splits to two non empty parts of text
# "how are you" -> [("how", "are you"), ("how are", "you")]
# (will also convert each sequence of whitespaces to one space)
def possible_splits(text: str):
    if not text:
        return []
    l = text.split()
    for i in range(1, len(l)):
        yield ' '.join(l[:i]), ' '.join(l[i:])


def interpretation_dict(street, city, format_factor=1, num=''):
    return {'street': street, 'num': num, 'city': city, 'matching_cities': get_matching_cities(city), 'format_factor': format_factor}


# returns a list of dicts with street, num, city
def get_possible_separations(text):
    if not text or text.isspace():
        return []
    text = text.strip()

    # <STREET>, <CITY> <NUM>
    num_after = number_after_formatted_address_re.match(text)
    if num_after:
        d = num_after.groupdict()
        d['matching_cities'] = get_matching_cities(d['city'])
        if d['matching_cities']:
            return [d]

    # <STREET>[ <NUM>],[ <CITY>]
    full_match = full_address_re.match(text)        # with comma
    if full_match:
        d = full_match.groupdict()
        d['matching_cities'] = get_matching_cities(d['city'])
        # unlike with other interpretations, in this case if there are no
        # matching cities, all matching streets will be shown
        return [d]

    # <STREET> <NUM> <CITY>
    no_comma = address_no_comma_re.match(text)
    if no_comma:            # the text is "street num city"
        d = no_comma.groupdict()
        d['matching_cities'] = get_matching_cities(d['city'])
        return [d]

    results = []
    street_with_num = street_with_num_re.match(text)
    if street_with_num:     # the text is "<street> <num>"
        # <STREET> <NUM>
        street_dict = street_with_num.groupdict()
        street_dict['city'] = ''
        street_dict['matching_cities'] = []
        results.append(street_dict)

        # <CITY> <STREET> <NUM>
        st_text = street_dict['street']
        for city, street in possible_splits(st_text):
            d = interpretation_dict(street, city, 0.15)
            if d['matching_cities']:
                # only consider this interpretation if there are possible cities
                results.append(d)
        return results

    # <STREET>
    results.append({'street': text, 'num': '', 'city': '', 'matching_cities': []})     # the text is just the street
    # not supporting just city for now:
    # results.append({'street': '', 'num': '', 'city': text})   # the text is just the city
    for start, end in possible_splits(text):
        # <STREET> <CITY>
        d = interpretation_dict(start, end, 0.5)
        if d['matching_cities']:
            # only consider this interpretation if there are possible cities
            results.append(d)

        # "<CITY> <STREET>"
        d = interpretation_dict(end, start, 0.2)
        if d['matching_cities']:
            # only consider this interpretation if there are possible cities
            results.append(d)
    return results


def words_contained(containing: str, contained:str):
    pass


# returns list
def get_matching_cities(city):
    if not city:
        return []
    if not cities[cities['city_name'] == city].empty:   # city name exists
        return [city]
    if len(city) < 2:
        contains = cities[cities['city_name'].str.startswith(city)]
    else:
        contains = cities[cities['city_name'].str.contains(city, regex=False)]
    if not contains.empty:  # contained in the names of cities
        return list(contains['city_name'])
    # TODO: words_contained
    return []


def fix_cities(dicts: list):
    return [dict(d, **{'city_input': d['city'], 'city': found_city}) for d in dicts for found_city in get_matching_cities(d['city'])[:5]]


def build_suggestions(dicts, max_num=15):
    dfs = collect_dfs(dicts, max_num)
    return prepare_results(dfs, max_num)


# gets dictionaries representing interpretations of the user input
# return a list with a DataFrame of results for each dict
def collect_dfs(dicts, max_num=15):
    streets_dfs = []
    num_res = 0
    for d in dicts:
        street = d['street']
        matching_cities = d['matching_cities']
        if street:
            street = street.strip()
            if len(street) == 1:    # if just one letter, use startswith and only take first 5 results
                if matching_cities:            # have city so also filter city
                    df = streets[streets['is_official_name'] & (streets['city_name'].isin(matching_cities))
                                 & streets['street_name'].str.startswith(street)].head(5)
                else:               # city is empty string so don't bother filtering city
                    df = streets[streets['is_official_name']
                                 & streets['street_name'].str.startswith(street)].head(5)
            else:                   # if more letters, use contain
                if matching_cities:            # have city so also filter city
                    df = streets[streets['city_name'].isin(matching_cities)
                                 & streets['street_name'].str.contains(d['street'], regex=False)]
                else:               # city is empty string so don't bother filtering city
                    df = streets[streets['street_name'].str.contains(d['street'], regex=False)]

            df['num'] = d['num'].strip() if 'num' in d and d['num'] else ''
            df['street_input'] = street
            df['city_input'] = d['city'] if d['city'] else ''
            df['format_factor'] = d['format_factor'] if 'format_factor' in d else 1
            streets_dfs.append(df)
            len_df = len(df)
            num_res += len_df  # we still don't now how many unique results
            if len_df >= max_num or num_res > max_num * 2:
                break
    return streets_dfs


# gets list of DFs, removes redundancies (duplicates, synonyms), formats address
# returns list of dicts with suggestions
def prepare_results(dfs_list, max_num):
    streets_suggestions = []
    if dfs_list:
        res_df = pd.concat(dfs_list).drop_duplicates()                  # make one DF
        if res_df.empty:
            return []
        res_df['street_similarity'] = res_df.apply(lambda row: similar(row['street_name'], row['street_input']), axis=1)
        res_df['city_similarity'] = res_df.apply(lambda row: similar(row['city_name'], row['city_input']), axis=1)
        res_df['score'] = (res_df['street_similarity'] + res_df['city_similarity'] + res_df['pop_score']) * res_df['format_factor'] * res_df['official_factor']
        res_df.drop(['pop_score', 'official_factor'], axis=1, inplace=True)         # unnecessary columns
        # sort by score, and for each street only keep result with highest score
        res_df = res_df.sort_values(by='score', ascending=False).drop_duplicates(['city_code', 'official_code']).head(max_num)
        # res_df['index'] = res_df.reset_index().index
        format_address_row = lambda row: row['street_name'] + (' ' + row['num'] if row['num'] else '') + ', ' + row['city_name']
        res_df['formatted_address'] = res_df.apply(format_address_row, axis=1)
        streets_suggestions = res_df.to_dict('records')
    return streets_suggestions


def get_suggestions(text: str, max_num=20):
    dicts = get_possible_separations(text)
    return build_suggestions(dicts, max_num)
